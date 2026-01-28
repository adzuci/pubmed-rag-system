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

output "rag_api_endpoint" {
  description = "HTTP API endpoint for the RAG Lambda."
  value       = aws_apigatewayv2_api.rag_api.api_endpoint
}

output "streamlit_cloudfront_url" {
  description = "Streamlit CloudFront distribution URL."
  value       = module.streamlit_app.streamlit_cloudfront_distribution_url
}

output "streamlit_custom_domain" {
  description = "Custom domain for the Streamlit app."
  value       = var.streamlit_domain_name
}

output "streamlit_custom_cloudfront_url" {
  description = "Custom CloudFront distribution URL for the Streamlit app."
  value       = "https://${aws_cloudfront_distribution.streamlit_custom.domain_name}"
}

output "route53_zone_name_servers" {
  description = "Name servers for the mamoru.org hosted zone."
  value       = length(aws_route53_zone.mamoru) > 0 ? aws_route53_zone.mamoru[0].name_servers : []
}

output "pubmed_ingest_lambda_name" {
  description = "Lambda function name for PubMed ingest."
  value       = aws_lambda_function.pubmed_ingest.function_name
}
