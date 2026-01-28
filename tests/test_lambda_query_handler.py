import json
from types import SimpleNamespace

from api import lambda_query_handler as query_handler


class DummyClient:
    def __init__(self, response):
        self._response = response

    def retrieve_and_generate(self, **kwargs):  # noqa: D401
        """Return a canned Bedrock response."""
        self.last_kwargs = kwargs
        return self._response


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
