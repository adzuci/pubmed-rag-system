module "bedrock" {
  source  = "aws-ia/bedrock/aws"
  version = "~> 0.0.33"

  create_agent = false

  create_default_kb = true
  kb_name           = "pubmed-rag-knowledge-base"
  kb_description    = "Knowledge base for PubMed RAG system with processed articles"

  create_s3_data_source      = true
  kb_s3_data_source          = aws_s3_bucket.data.arn
  s3_inclusion_prefixes      = [var.processed_prefix]
  data_deletion_policy       = "RETAIN"

  number_of_shards   = "2"
  number_of_replicas = "0"

  tags = var.tags
}