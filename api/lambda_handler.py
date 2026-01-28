import base64
import json
import os

import boto3


KB_ID = os.getenv("BEDROCK_KB_ID", "")
MODEL_ARN = os.getenv(
    "BEDROCK_MODEL_ARN",
    "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-5-sonnet-20240620-v1:0",
)

client = boto3.client("bedrock-agent-runtime")


def _json_response(status_code, payload):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
        },
        "body": json.dumps(payload),
    }


def _extract_question(event):
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
    if not KB_ID:
        return _json_response(500, {"error": "BEDROCK_KB_ID is not configured"})

    question = _extract_question(event)
    if not question:
        return _json_response(400, {"error": "Missing question"})

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
                },
            },
        )
    except Exception as exc:
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
