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
