resource "aws_secretsmanager_secret" "ncbi_credentials" {
  name        = "pubmed-ncbi-credentials"
  description = "NCBI credentials for PubMed ingest (email + optional API key)."
  tags        = var.tags
}

resource "aws_secretsmanager_secret_version" "ncbi_credentials" {
  secret_id = aws_secretsmanager_secret.ncbi_credentials.id
  secret_string = jsonencode({
    ncbi_email   = var.ncbi_email
    ncbi_api_key = var.ncbi_api_key
  })
}
