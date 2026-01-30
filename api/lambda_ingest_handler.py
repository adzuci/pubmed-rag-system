"""PubMed ingest Lambda: search PubMed, fetch MEDLINE, and drop raw .txt into S3.

We pull NCBI credentials from Secrets Manager, run ESearch/EFetch (same idea as the
notebook), and write one formatted .txt per PMID under the bucket's raw/ prefix.
Configure via NCBI_SECRET_ARN, S3_BUCKET; optional PUBMED_QUERY, RETMAX, BATCH_SIZE, RAW_PREFIX.
"""

import json
import logging
import os
import time

import boto3
from botocore.exceptions import ClientError

try:
    from Bio import Entrez, Medline
except Exception as exc:  # pragma: no cover - runtime dependency check
    raise RuntimeError(
        "Biopython is required for PubMed ingest. Package it with the Lambda."
    ) from exc

LOGGER = logging.getLogger("pubmed-ingest")
LOGGER.setLevel(logging.INFO)


# --- Secrets ---
def _get_secret_value(secret_arn):
    """Load the secret from Secrets Manager and return it as a dict (JSON string or binary)."""
    client = boto3.client("secretsmanager")
    resp = client.get_secret_value(SecretId=secret_arn)
    if "SecretString" in resp:
        return json.loads(resp["SecretString"])
    return json.loads(resp["SecretBinary"].decode("utf-8"))


# --- Record formatting ---
def _format_record(rec):
    """Turn one parsed MEDLINE record into the same .txt-style block we use in the notebook."""
    parts = []
    if rec.get("PMID"):
        parts.append(f"PMID: {rec['PMID']}")
    if rec.get("TI"):
        parts.append(f"Title: {rec['TI']}")
    if rec.get("AU"):
        parts.append(f"Authors: {', '.join(rec['AU'])}")
    if rec.get("JT"):
        parts.append(f"Journal: {rec['JT']}")
    if rec.get("DP"):
        parts.append(f"Date: {rec['DP']}")
    if rec.get("AB"):
        parts.append(f"Abstract:\n{rec['AB']}")
    return "\n".join(parts).strip()


def handler(event, context):
    """Run the full ingest: search, fetch in batches, write .txt files to S3."""
    del event  # unused

    # --- Config and validation ---
    secret_arn = os.getenv("NCBI_SECRET_ARN", "")
    bucket = os.getenv("S3_BUCKET", "")
    raw_prefix = os.getenv("RAW_PREFIX", "raw/").rstrip("/") + "/"

    query = os.getenv(
        "PUBMED_QUERY",
        '("Dementia"[Mesh] OR "Mild Cognitive Impairment"[Mesh]) '
        'AND ("Decision Support Systems, Clinical"[Mesh] OR "Caregivers"[Mesh] '
        'OR caregiver*[tiab] OR "decision support"[tiab])',
    )
    retmax = int(os.getenv("RETMAX", "500"))
    batch_size = int(os.getenv("BATCH_SIZE", "100"))

    if not secret_arn:
        raise ValueError("NCBI_SECRET_ARN must be set")
    if not bucket:
        raise ValueError("S3_BUCKET must be set")

    secret = _get_secret_value(secret_arn)
    email = secret.get("ncbi_email") or secret.get("NCBI_EMAIL")
    api_key = secret.get("ncbi_api_key") or secret.get("NCBI_API_KEY") or ""
    if not email:
        raise ValueError("NCBI email missing in secret")

    Entrez.email = email
    if api_key:
        Entrez.api_key = api_key

    # NCBI allows more requests/sec with an API key; use shorter delay when key is set.
    request_delay = 0.10 if api_key else 0.34
    s3 = boto3.client("s3")

    # --- PubMed search (ESearch) ---
    try:
        stream = Entrez.esearch(db="pubmed", term=query, retmax=retmax, usehistory="y")
        record = Entrez.read(stream)
        stream.close()
    except Exception as exc:
        LOGGER.exception("pubmed_search_failed")
        raise RuntimeError(f"PubMed search failed: {exc}") from exc

    webenv = record.get("WebEnv")
    query_key = record.get("QueryKey")
    total_count = int(record.get("Count", 0))
    target_count = min(retmax, total_count)

    if not (webenv and query_key):
        raise RuntimeError("Missing WebEnv or QueryKey from PubMed search.")

    # --- Fetch in batches and write to S3 (EFetch) ---
    written = 0
    for start in range(0, target_count, batch_size):
        # Leave enough time for this batch and a clean shutdown.
        if context and context.get_remaining_time_in_millis() < 15000:
            LOGGER.warning("Stopping early to avoid Lambda timeout.")
            break

        stream = Entrez.efetch(
            db="pubmed",
            rettype="medline",
            retmode="text",
            retstart=start,
            retmax=min(batch_size, target_count - start),
            webenv=webenv,
            query_key=query_key,
        )
        try:
            for rec in Medline.parse(stream):
                pmid = rec.get("PMID")
                if not pmid:
                    continue
                text = _format_record(rec)
                if not text:
                    continue
                key = f"{raw_prefix}{pmid}.txt"
                s3.put_object(Bucket=bucket, Key=key, Body=text.encode("utf-8"))
                written += 1
        finally:
            stream.close()

        if start + batch_size < target_count:
            time.sleep(request_delay)

    # --- Response ---
    LOGGER.info("pubmed_ingest_complete: %s records", written)
    return {
        "statusCode": 200,
        "body": json.dumps(
            {
                "written": written,
                "target_count": target_count,
                "bucket": bucket,
                "raw_prefix": raw_prefix,
            }
        ),
    }
