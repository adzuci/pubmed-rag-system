"""RAG query Lambda: answers questions using the Bedrock knowledge base.

API Gateway sends the request here; we call Bedrock retrieve_and_generate so the
model can search our PubMed-derived index and answer from those sources. Needs
BEDROCK_KB_ID; BEDROCK_MODEL_ARN is optional and has a default.
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


def _parse_body(event):
    """Get the request body as a dict; handles base64 if the event says so."""
    if not event.get("body"):
        return {}
    body = event["body"]
    if event.get("isBase64Encoded"):
        body = base64.b64decode(body).decode("utf-8")
    try:
        return json.loads(body)
    except json.JSONDecodeError:
        return None


def _extract_question(event):
    """Extract the `question` string from a REST or HTTP API event."""
    data = _parse_body(event)
    if data is not None and data.get("question") is not None:
        return data.get("question")
    params = event.get("queryStringParameters") or {}
    return params.get("question")


def _extract_client_ip(event):
    """Optional client_ip from the body (the Streamlit UI sends it for logging)."""
    data = _parse_body(event)
    if data is None:
        return None
    return data.get("client_ip")


def handler(event, context):
    """Handle a single RAG query: validate, call Bedrock, return answer and sources."""
    del context  # unused

    if not KB_ID:
        return _json_response(500, {"error": "BEDROCK_KB_ID is not configured"})

    question = _extract_question(event)
    if not question:
        return _json_response(400, {"error": "Missing question"})

    client_ip = _extract_client_ip(event) or "-"
    LOGGER.info("rag_query: %s %s", client_ip, question)

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

CRITICAL INSTRUCTIONS:
- Be concise when appropriate
- Do NOT mention "Source 1", "Source 2", etc. in your response
- Do NOT reference sources by number or name
- Do NOT say "the sources show" or "according to the sources"
- Simply provide the answer directly, as if you are stating facts
- Be clear and empathetic
- Focus on the most relevant findings
- If sources don't address the question, say so briefly

The sources will be displayed separately below your answer, so do not reference them in your text.

Retrieved sources:
$search_results$

Question: $input$

Provide a direct answer without mentioning sources:"""
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

    if not sources:
        try:
            retrieval = client.retrieve(
                knowledgeBaseId=KB_ID,
                retrievalQuery={"text": question},
                retrievalConfiguration={
                    "vectorSearchConfiguration": {"numberOfResults": 5}
                },
            )
            for item in retrieval.get("retrievalResults", []):
                sources.append(
                    {
                        "text": item.get("content", {}).get("text", ""),
                        "metadata": item.get("metadata", {}),
                    }
                )
        except Exception:
            LOGGER.exception("rag_query_retrieve_failed")

    return _json_response(
        200,
        {
            "answer": answer,
            "sources": sources,
        },
    )
