import base64
import json
import os
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

# Set AWS region before importing to avoid NoRegionError
os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")
os.environ.setdefault("AWS_REGION", "us-east-1")

# Mock boto3.client before importing the handler module to prevent NoRegionError
mock_boto3_client = MagicMock()
with patch("boto3.client", return_value=mock_boto3_client):
    from api import lambda_query_handler as query_handler


class DummyClient:
    def __init__(self, response, retrieval_response=None):
        self._response = response
        self._retrieval_response = retrieval_response or {}

    def retrieve_and_generate(self, **kwargs):  # noqa: D401
        """Return a canned Bedrock response."""
        self.last_kwargs = kwargs
        return self._response

    def retrieve(self, **kwargs):  # noqa: D401
        """Return a canned Bedrock retrieve response."""
        self.retrieve_kwargs = kwargs
        return self._retrieval_response


def test_handler_returns_answer_and_sources(monkeypatch):
    response = {
        "output": {"text": "Test answer."},
        "citations": [
            {
                "retrievedReferences": [
                    {
                        "content": {"text": "Doc text."},
                        "metadata": {"pmid": "123"},
                    }
                ]
            }
        ],
    }

    client = DummyClient(response)
    monkeypatch.setattr(query_handler, "client", client)
    # The handler reads KB_ID at import time, so patch the module
    # variable directly instead of relying only on environment.
    monkeypatch.setattr(query_handler, "KB_ID", "kb-123")

    event = {
        "body": json.dumps({"question": "What is dementia?"}),
        "isBase64Encoded": False,
    }

    result = query_handler.handler(event, SimpleNamespace())
    assert result["statusCode"] == 200
    body = json.loads(result["body"])
    assert body["answer"] == "Test answer."
    assert body["sources"][0]["metadata"]["pmid"] == "123"


def test_handler_falls_back_to_retrieve_when_no_citations(monkeypatch):
    response = {
        "output": {"text": "Test answer."},
        "citations": [],
    }
    retrieval_response = {
        "retrievalResults": [
            {
                "content": {"text": "Doc text."},
                "metadata": {"pmid": "456"},
            }
        ]
    }

    client = DummyClient(response, retrieval_response)
    monkeypatch.setattr(query_handler, "client", client)
    monkeypatch.setattr(query_handler, "KB_ID", "kb-123")

    event = {
        "body": json.dumps({"question": "What is dementia?"}),
        "isBase64Encoded": False,
    }

    result = query_handler.handler(event, SimpleNamespace())
    assert result["statusCode"] == 200
    body = json.loads(result["body"])
    assert body["answer"] == "Test answer."
    assert body["sources"][0]["metadata"]["pmid"] == "456"


def test_handler_returns_500_when_kb_missing(monkeypatch):
    monkeypatch.setattr(query_handler, "KB_ID", "")
    event = {
        "body": json.dumps({"question": "What is dementia?"}),
        "isBase64Encoded": False,
    }
    result = query_handler.handler(event, SimpleNamespace())
    assert result["statusCode"] == 500


def test_handler_returns_400_on_invalid_json(monkeypatch):
    monkeypatch.setattr(query_handler, "KB_ID", "kb-123")
    event = {"body": "{", "isBase64Encoded": False}
    result = query_handler.handler(event, SimpleNamespace())
    assert result["statusCode"] == 400


def test_handler_accepts_base64_body(monkeypatch):
    response = {
        "output": {"text": "Test answer."},
        "citations": [],
    }
    client = DummyClient(response, retrieval_response={"retrievalResults": []})
    monkeypatch.setattr(query_handler, "client", client)
    monkeypatch.setattr(query_handler, "KB_ID", "kb-123")

    payload = json.dumps({"question": "What is dementia?", "client_ip": "1.2.3.4"})
    encoded = base64.b64encode(payload.encode("utf-8")).decode("utf-8")
    event = {"body": encoded, "isBase64Encoded": True}

    result = query_handler.handler(event, SimpleNamespace())
    assert result["statusCode"] == 200
