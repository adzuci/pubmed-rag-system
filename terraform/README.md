# Terraform

This folder will contain all Terraform for the AWS infrastructure for this project.
Currently it manages the S3 bucket for PubMed data plus Bedrock Knowledge Base resources:
- `raw/`
- `processed/`

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
