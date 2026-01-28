# Terraform

This folder contains Terraform for the AWS infrastructure for this project.
It manages:
- S3 bucket for PubMed data (`raw/` and `processed/` prefixes)
- Bedrock Knowledge Base and S3 data source
- Lambda-backed HTTP API for RAG queries
- PubMed ingest Lambda that writes raw MEDLINE text into S3
- Serverless Streamlit UI and optional custom domain (Route53 + CloudFront)

## Quick start
1. `terraform init`
2. `terraform plan`
3. `terraform apply`

## State + locking
Local state is used by default. For team use or production, configure remote state
and a lock table, e.g.:
- **S3 backend** for state
- **DynamoDB** for state locking

Example backend config (put in `backend.tf` or pass via `-backend-config`):
```
terraform {
  backend "s3" {
    bucket         = "your-tf-state-bucket"
    key            = "pubmed-rag-system/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform-locks"
    encrypt        = true
  }
}
```

## Inputs
- `aws_region` (default: `us-east-1`)
- `bucket_name` (required)
- `raw_prefix` (default: `raw/`)
- `processed_prefix` (default: `processed/`)
- `tags` (default: `project=pubmed-rag-system`, `env=production`)
- `ncbi_email` (required)
- `ncbi_api_key` (optional)
- `bedrock_model_arn` (default: Claude 3.5 Sonnet)
- `rag_api_name` (default: `pubmed-rag-api`)
- `streamlit_app_name` (default: `pubmed-rag-ui`)
- `streamlit_app_version` (default: `v0.0.2`)
- `opensearch_admin_principals` (list of IAM principals for OpenSearch access)
- `streamlit_domain_name` (default: `mamoru.org`)
- `streamlit_hosted_zone_id` (optional, use an existing Route53 zone)
- `streamlit_cf_header_name` (default: `X-Verify-Origin`)
- `streamlit_cf_header_value` (default: `streamlit-CloudFront-Distribution`)
- `alert_email` (default: `adam@blackwell.ai`)
- `pubmed_query` (default: dementia caregiving query string)
- `pubmed_retmax` (default: `500`)
- `pubmed_batch_size` (default: `100`)

## Bedrock Knowledge Base
This module also provisions an Amazon Bedrock Knowledge Base using the
`aws-ia/bedrock/aws` module, with:
- Vector store: OpenSearch Serverless (auto-created)
- Data source: S3 bucket scoped to `processed/` (points at `bucket_name`)
- Embedding model: Amazon Titan Embed Text v2 (module default)

Key outputs to note (see `terraform/outputs.tf`):
- `bedrock_kb_id`
- `bedrock_s3_data_source_arn`
- `bedrock_s3_data_source_name`
- `bedrock_kb_role_name`
- `opensearch_collection_endpoint`
- `rag_api_endpoint`
- `streamlit_cloudfront_url`
- `streamlit_custom_domain`
- `streamlit_custom_cloudfront_url`
- `route53_zone_name_servers`
- `pubmed_ingest_lambda_name`

## PubMed ingest Lambda
Terraform defines a dedicated Lambda (`pubmed_ingest`) that:
- Reads NCBI credentials from Secrets Manager (`ncbi_credentials` secret)
- Executes a PubMed query via Biopython Entrez
- Writes MEDLINE-derived text files to `s3://<bucket_name>/<raw_prefix>/`

It is not scheduled by default. Trigger it manually, e.g.:
- `aws lambda invoke --function-name $(terraform output -raw pubmed_ingest_lambda_name) --payload '{}' /tmp/ingest.json`

To add a schedule, create an EventBridge rule and target in a follow-up change
so you can control cadence and cost explicitly.

## Rate limiting
The HTTP API stage applies default throttling (burst 10, rate 2 RPS). If you need
stronger protections, add AWS WAF rate-based rules in front of API Gateway or
CloudFront later.

## Alarms
Terraform configures CloudWatch alarms for:
- Lambda Errors (RAG API)
- ALB Target 5XX (Streamlit)
Alerts are sent to the SNS topic subscribed by `alert_email`.
