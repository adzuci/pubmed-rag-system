# Terraform (S3)

This folder will contain all Terraform for the AWS infrastructure for this project.
Currently it manages the single S3 bucket for PubMed data with two logical prefixes:
- `raw/`
- `processed/`

## Quick start
1. `terraform init`
2. `terraform plan`
3. `terraform apply`

Note: In a production setup I would use remote state with DynamoDB locks, but I’m keeping state local for now.

## Inputs
- `aws_region` (default: `us-east-1`)
- `bucket_name` (default: `pubmed-rag-data`)
- `raw_prefix` (default: `raw/`)
- `processed_prefix` (default: `processed/`)
- `tags` (default: `{}`)

## Bedrock Knowledge Base
This module also provisions an Amazon Bedrock Knowledge Base using the
`aws-ia/bedrock/aws` module, with:
- Vector store: OpenSearch Serverless (auto-created)
- Data source: S3 bucket scoped to `processed/`
- Embedding model: Amazon Titan Embed Text v2 (module default)

Key outputs to note:
- Knowledge base identifier
- S3 data source ARN
- Knowledge base IAM role name
