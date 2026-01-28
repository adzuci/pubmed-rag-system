module "bedrock" {
  source  = "aws-ia/bedrock/aws"
  version = "~> 0.0.33"

  create_agent = false

  enable_bedrock           = true
  create_service_role      = true
  service_role_name        = "pubmed-rag-bedrock"
  service_role_description = "Bedrock role for PubMed RAG"

  create_default_kb = true
  kb_name           = "pubmed-rag-knowledge-base"
  kb_description    = "Knowledge base for PubMed RAG system with processed articles"

  create_s3_data_source      = true
  s3_data_source_bucket_name = aws_s3_bucket.data.id
  s3_inclusion_prefixes      = [var.processed_prefix]
  data_deletion_policy       = "RETAIN"

  tags = var.tags
}