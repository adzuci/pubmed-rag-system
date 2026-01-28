# PubMed RAG System

This project builds a retrieval-augmented generation (RAG) system over PubMed to answer caregiver- and clinician-oriented questions about dementia progression and care using peer-reviewed clinical literature.

## Overview
- Ingest PubMed articles with NCBI E-utilities and store raw/processed data in S3.
- Chunk and embed text with AWS Bedrock and store vectors in Bedrock Knowledge Bases.
- Serve a single-turn Q&A endpoint via AWS Lambda + API Gateway.
- Provide a minimal Streamlit UI for querying with sources.

## Repository Layout
- `ingest/`: PubMed fetch scripts and helpers.
- `processing/`: Chunking, embeddings, and indexing.
- `rag/`: Retrieval and prompt assembly logic.
- `api/`: Inference handler (Lambda entrypoint).
- `ui/`: Streamlit app.
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
3. Launch Jupyter Notebook (no Lab required):
   - `jupyter notebook`
4. Open `notebooks/pubmed_search_stub.ipynb` and run the cells.


Notes:
- Respect NCBI rate limits.
- Keep the fetched corpus small to stay within the assignment scope.

## Project checklist
- [x] Local PubMed ingest (Jupyter notebook)
- [ ] Repo scaffolding and config
- [ ] Terraform: S3 buckets (raw + processed)
- [ ] Upload raw PubMed data to S3
- [ ] Enable AWS Bedrock and IAM permissions
- [ ] Embedding + vector index job
- [ ] RAG retrieval and answer logic (local)
- [ ] Lambda inference API (API Gateway)
- [ ] Streamlit app (local)
- [ ] Deploy Streamlit with terraform-aws-serverless-streamlit-app
- [ ] Route 53 domain + HTTPS
- [ ] README, demo prep, and design explanations

## Deployment
Minimal AWS services (details to be documented in this repo):
- **S3** for raw/processed corpus storage
- **Bedrock Knowledge Bases** for vector storage and retrieval
- **Bedrock** for embeddings + LLM
- **Lambda + API Gateway** for scalable inference endpoint
- **Streamlit** for UI (local or hosted)

Reference: https://docs.aws.amazon.com/prescriptive-guidance/latest/choosing-an-aws-vector-database-for-rag-use-cases/vector-db-options.html

## ADRs
Create ADRs in `docs/adr/` to capture key decisions (e.g., chunk size, embedding model, vector DB choice).
