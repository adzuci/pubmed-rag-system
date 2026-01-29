"""Lambda handler for RAG query requests.

This function is fronted by API Gateway and calls Bedrock
`retrieve_and_generate` against a configured knowledge base.

Environment variables:
    BEDROCK_KB_ID: Knowledge base identifier (required).
    BEDROCK_MODEL_ARN: Model ARN to use for generation (optional, has default).
"""

import base64
import json
import logging
import os

import boto3

LOGGER = logging.getLogger("rag-query")
LOGGER.setLevel(logging.INFO)

KB_ID = os.getenv("BEDROCK_KB_ID", "")
MODEL_ARN = os.getenv(
    "BEDROCK_MODEL_ARN",
    "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-5-sonnet-20240620-v1:0",
)

client = boto3.client("bedrock-agent-runtime")


def _json_response(status_code, payload):
    """Return an API Gateway compatible JSON response."""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
        },
        "body": json.dumps(payload),
    }


def _extract_question(event):
    """Extract the `question` string from a REST or HTTP API event."""
    if event.get("body"):
        body = event["body"]
        if event.get("isBase64Encoded"):
            body = base64.b64decode(body).decode("utf-8")
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            return None
        return data.get("question")
    params = event.get("queryStringParameters") or {}
    return params.get("question")


def handler(event, context):
    """Entry point for the query Lambda."""
    del context  # unused

    if not KB_ID:
        return _json_response(500, {"error": "BEDROCK_KB_ID is not configured"})

    question = _extract_question(event)
    if not question:
        return _json_response(400, {"error": "Missing question"})

    LOGGER.info("rag_query: %s", question)

    try:
        resp = client.retrieve_and_generate(
            input={"text": question},
            retrieveAndGenerateConfiguration={
                "type": "KNOWLEDGE_BASE",
                "knowledgeBaseConfiguration": {
                    "knowledgeBaseId": KB_ID,
                    "modelArn": MODEL_ARN,
                    "retrievalConfiguration": {
                        "vectorSearchConfiguration": {"numberOfResults": 5}
                    },
                    "generationConfiguration": {
                        "promptTemplate": {
                            "textPromptTemplate": """You are Mamoru, a compassionate and knowledgeable assistant helping caregivers and clinicians understand dementia care based on peer-reviewed clinical literature from PubMed.

Your role is to:
- Provide evidence-based answers using only the information from the retrieved sources
- Be clear and empathetic, recognizing the challenges caregivers and families face
- Cite specific studies or findings when relevant
- Offer actionable recommendations when the evidence supports them
- Acknowledge when the available sources don't contain enough information to fully answer the question

Use the retrieved sources to ground your response. If the sources don't directly address the question, say so honestly rather than speculating.

Retrieved sources:
$search_results$

Question: $input$

Based on the provided sources, please answer the question above."""
                        }
                    },
                },
            },
        )
    except Exception as exc:
        LOGGER.exception("rag_query_failed")
        return _json_response(500, {"error": str(exc)})

    answer = resp.get("output", {}).get("text", "")
    sources = []
    for citation in resp.get("citations", []):
        for ref in citation.get("retrievedReferences", []):
            sources.append(
                {
                    "text": ref.get("content", {}).get("text", ""),
                    "metadata": ref.get("metadata", {}),
                }
            )

    return _json_response(
        200,
        {
            "answer": answer,
            "sources": sources,
        },
    )
