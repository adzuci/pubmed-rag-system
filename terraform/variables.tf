variable "aws_region" {
  description = "AWS region for resources."
  type        = string
  default     = "us-east-1"
}

variable "bucket_name" {
  description = "S3 bucket for PubMed data (raw + processed prefixes)."
  type        = string
}

variable "raw_prefix" {
  description = "Prefix for raw PubMed data within the bucket."
  type        = string
  default     = "raw/"
}

variable "processed_prefix" {
  description = "Prefix for processed PubMed data within the bucket."
  type        = string
  default     = "processed/"
}

variable "tags" {
  description = "Tags to apply to the S3 bucket."
  type        = map(string)
  default     = {
    project = "pubmed-rag-system"
    env     = "production"
  }
}

variable "ncbi_email" {
  description = "NCBI email for Entrez API usage."
  type        = string
  sensitive   = true
}

variable "ncbi_api_key" {
  description = "NCBI API key (optional)."
  type        = string
  sensitive   = true
  default     = ""
}

variable "bedrock_model_arn" {
  description = "Bedrock model ARN used for retrieve-and-generate."
  type        = string
  default     = "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-5-sonnet-20240620-v1:0"
}

variable "rag_api_name" {
  description = "Name prefix for the RAG API."
  type        = string
  default     = "pubmed-rag-api"
}

variable "streamlit_app_name" {
  description = "Name prefix for the Streamlit app."
  type        = string
  default     = "pubmed-rag-ui"
}

variable "streamlit_app_version" {
  description = "Version tag for the Streamlit app container."
  type        = string
  default     = "v0.0.6"
}

variable "opensearch_admin_principals" {
  description = "Additional OpenSearch Serverless principals allowed to manage the KB collection/index."
  type        = list(string)
  default     = []
}

variable "streamlit_domain_name" {
  description = "Custom domain name for the Streamlit app."
  type        = string
  default     = "mamoruproject.org"
}

variable "streamlit_hosted_zone_id" {
  description = "Existing Route53 hosted zone ID for the Streamlit domain (leave empty to create)."
  type        = string
  default     = "Z06494003JKCM4RYNM7JX"
}

variable "streamlit_cf_header_name" {
  description = "CloudFront custom header name for ALB origin."
  type        = string
  default     = "X-Verify-Origin"
}

variable "streamlit_cf_header_value" {
  description = "CloudFront custom header value for ALB origin."
  type        = string
  default     = "streamlit-CloudFront-Distribution"
}

variable "opensearch_endpoint" {
  description = "Override OpenSearch endpoint for imports (optional)."
  type        = string
  default     = ""
}

variable "alert_email" {
  description = "Email address for CloudWatch alarm notifications."
  type        = string
  default     = "adam@blackwell.ai"
}

variable "pubmed_query" {
  description = "PubMed query for ingestion."
  type        = string
  default     = <<EOT
("Dementia"[Mesh] OR "Mild Cognitive Impairment"[Mesh]) AND ("Decision Support Systems, Clinical"[Mesh] OR "Caregivers"[Mesh] OR caregiver*[tiab] OR "decision support"[tiab])
EOT
}

variable "pubmed_retmax" {
  description = "Max number of PubMed records to ingest."
  type        = number
  default     = 500
}

variable "pubmed_batch_size" {
  description = "Batch size for PubMed efetch."
  type        = number
  default     = 100
}

