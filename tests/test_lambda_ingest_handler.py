import json
from types import SimpleNamespace

from api import lambda_ingest_handler as ingest_handler


class DummySecretsClient:
    def __init__(self, secret):
        self._secret = secret

    def get_secret_value(self, SecretId):  # noqa: N803,D401
        """Return a canned secret string."""
        return {"SecretString": json.dumps(self._secret)}


class DummyS3Client:
    def __init__(self):
        self.put_calls = []

    def put_object(self, **kwargs):  # noqa: D401
        """Record put_object calls."""
        self.put_calls.append(kwargs)


class DummyEntrezModule:
    def __init__(self, records):
        self._records = records
        self.email = None
        self.api_key = None

    def esearch(self, **kwargs):  # noqa: D401
        """Return a fake search handle."""
        self.last_esearch = kwargs

        class Handle:
            def close(self_non):
                return None

        return Handle()

    def read(self, stream):  # noqa: D401
        """Return a synthetic ESearch result."""
        del stream
        return {
            "WebEnv": "webenv",
            "QueryKey": "1",
            "Count": str(len(self._records)),
        }

    def efetch(self, **kwargs):  # noqa: D401
        """Return a fake efetch stream."""
        self.last_efetch = kwargs

        class Handle:
            def __init__(self, records):
                self._records = records

            def close(self):
                return None

        return Handle(self._records)


class DummyMedline:
    @staticmethod
    def parse(handle):  # noqa: D401
        """Yield records from the dummy handle."""
        yield from handle._records


def test_format_record_includes_required_fields():
    rec = {
        "PMID": "123",
        "TI": "Title",
        "AU": ["A", "B"],
        "JT": "Journal",
        "DP": "2025",
        "AB": "Abstract",
    }
    text = ingest_handler._format_record(rec)
    assert "PMID: 123" in text
    assert "Title: Title" in text
    assert "Authors: A, B" in text
    assert "Journal: Journal" in text
    assert "Date: 2025" in text
    assert "Abstract:" in text


def test_handler_writes_records_to_s3(monkeypatch):
    secret = {"ncbi_email": "you@example.com", "ncbi_api_key": ""}
    secrets_client = DummySecretsClient(secret)
    s3_client = DummyS3Client()
    entrez = DummyEntrezModule(
        records=[
            {"PMID": "1", "TI": "Title 1"},
            {"PMID": "2", "TI": "Title 2"},
        ]
    )

    monkeypatch.setenv("NCBI_SECRET_ARN", "arn:aws:secretsmanager:::secret/test")
    monkeypatch.setenv("S3_BUCKET", "bucket")
    monkeypatch.setenv("RAW_PREFIX", "raw/")

    monkeypatch.setattr(
        ingest_handler.boto3,
        "client",
        lambda service: secrets_client if service == "secretsmanager" else s3_client,
    )
    monkeypatch.setattr(ingest_handler, "Entrez", entrez)
    monkeypatch.setattr(ingest_handler, "Medline", DummyMedline)

    result = ingest_handler.handler(
        {}, SimpleNamespace(get_remaining_time_in_millis=lambda: 10_000_000)
    )

    assert result["statusCode"] == 200
    body = json.loads(result["body"])
    assert body["written"] == 2
    assert len(s3_client.put_calls) == 2
