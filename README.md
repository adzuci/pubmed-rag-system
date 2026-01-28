# PubMed RAG System

This project builds a retrieval-augmented generation (RAG) system over PubMed to answer caregiver and clinician-oriented questions about dementia progression and care using peer-reviewed clinical literature.

## Overview
- Ingest PubMed articles with NCBI E-utilities and store raw/processed data in S3.
- Chunk and embed text with AWS Bedrock and store vectors in Bedrock Knowledge Bases.
- Serve a single-turn Q&A endpoint via AWS Lambda + API Gateway.
- Provide a minimal Streamlit UI for querying with sources.

## Architecture Diagram
```mermaid
flowchart LR
  A[PubMed] -->|ESearch/EFetch| B[Local ingest notebook]
  B -->|raw text| S3Raw[(S3 raw/)]
  B -->|processed JSON| S3Processed[(S3 processed/)]
  S3Processed --> KB[Bedrock Knowledge Base]
  Q[User question] --> UI[Streamlit UI]
  UI --> API[API Gateway + Lambda]
  API --> KB
  API --> LLM[Bedrock LLM]
  KB --> API
  API --> UI
```

## Repository Layout
- `ingest/`: PubMed fetch scripts.
- `processing/`: Chunking, embeddings, and indexing.
- `rag/`: Retrieval and prompt assembly logic.
- `api/`: TBA.
- `ui/`: TBA Streamlit app.
- `docs/adr/`: Architecture Decision Records.
- `notebooks/`: Local exploration notebooks.

## Local Data Ingestion (Notebook)
You can run ingestion locally in a Jupyter notebook for quick iteration:

1. Create and activate a virtual environment, then install requirements:
   - `python -m venv .venv`
   - `source .venv/bin/activate`
   - `pip install -r requirements.txt`
2. Create a local `.env` (gitignored) with:
   - `NCBI_EMAIL=you@example.com`
   - `NCBI_API_KEY=your_key_here` (optional)
   - `S3_BUCKET=your-bucket` (for uploads)
   - `BEDROCK_KB_ID=kb-XXXXXXXXXX` (for RAG prototype)
   - `BEDROCK_MODEL_ARN=...` (optional, defaults in notebook)
3. Launch Jupyter Notebook (no Lab required):
   - `jupyter notebook`
4. Open `notebooks/pubmed_search_and_fetch.ipynb` and run the cells.

## Project checklist
- [x] Local PubMed ingest (Jupyter notebook)
- [x] Repo scaffolding and config
- [x] Terraform: S3 buckets (raw + processed)
- [x] Upload raw PubMed data to S3
- [x] Enable AWS Bedrock and IAM permissions
- [ ] RAG retrieval and answer logic
- [ ] Lambda inference API
- [ ] Streamlit app (local)
- [ ] Deploy Streamlit with terraform-aws-serverless-streamlit-app
- [ ] Route 53 domain + HTTPS
- [ ] README, demo prep, and design explanations

## Terraform (What It Provisions)
Current Terraform covers:
- **S3** bucket for raw/processed corpus storage
- **Bedrock Knowledge Base** (vector store backed by OpenSearch Serverless)
- **S3 data source** scoped to the `processed/` prefix
- **Secrets Manager** secret for NCBI credentials (`ncbi_email`, `ncbi_api_key`)

Tags are applied via the `tags` variable (default: `project=pubmed-rag-system`, `env=production`).

Required inputs:
- `bucket_name` (no default)
- `ncbi_email` (no default)

## Deployment
Minimal AWS services (details to be documented in this repo):
- **S3** for raw/processed corpus storage
- **Bedrock Knowledge Bases** for vector storage and retrieval
- **Bedrock** for embeddings + LLM
- **Lambda + API Gateway** for scalable inference endpoint
- **Streamlit** for UI (local or hosted)

## Secrets + Scheduling
- Secrets: store `NCBI_EMAIL` and `NCBI_API_KEY` in AWS Secrets Manager (no plaintext in repo).
- Scheduling: use EventBridge to trigger a Lambda (or ECS task) for periodic ingest.
- Details: `docs/ops/scheduled_ingest.md`

## Bedrock KB Ingestion
After uploading JSONL to `s3://<bucket>/processed/`, start an ingestion job:
- `aws bedrock-agent start-ingestion-job --knowledge-base-id <kb_id> --data-source-id <ds_id>`
- Check status with `aws bedrock-agent get-ingestion-job ...`

## RAG Prototype (Notebook)
Use `notebooks/pubmed_rag_prototype.ipynb` for local retrieval and answer generation.
Set `BEDROCK_KB_ID` (required) and optionally `BEDROCK_MODEL_ARN` in `.env`.

## ADRs
Create ADRs in `docs/adr/` to capture key decisions (e.g., chunk size, embedding model, vector DB choice).
