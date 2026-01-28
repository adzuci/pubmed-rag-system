output "bedrock_kb_id" {
  description = "Bedrock knowledge base identifier."
  value       = module.bedrock.default_kb_identifier
}

output "bedrock_s3_data_source_arn" {
  description = "Bedrock S3 data source ARN."
  value       = module.bedrock.s3_data_source_arn
}

output "bedrock_s3_data_source_name" {
  description = "Bedrock S3 data source name."
  value       = module.bedrock.s3_data_source_name
}

output "bedrock_kb_role_name" {
  description = "IAM role name used by the Bedrock knowledge base."
  value       = module.bedrock.knowledge_base_role_name
}

output "opensearch_collection_endpoint" {
  description = "OpenSearch Serverless collection endpoint (vector store)."
  value       = module.bedrock.default_collection.collection_endpoint
}
