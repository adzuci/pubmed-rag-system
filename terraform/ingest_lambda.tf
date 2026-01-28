data "archive_file" "pubmed_ingest_lambda" {
  type        = "zip"
  source_file = "${path.module}/../api/lambda_ingest_handler.py"
  output_path = "${path.module}/pubmed_ingest_lambda.zip"
}

data "aws_iam_policy_document" "pubmed_ingest_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "pubmed_ingest" {
  name               = "${var.rag_api_name}-ingest-role"
  assume_role_policy = data.aws_iam_policy_document.pubmed_ingest_assume.json
  tags               = var.tags
}

data "aws_iam_policy_document" "pubmed_ingest_policy" {
  statement {
    actions = [
      "s3:PutObject",
      "s3:PutObjectAcl",
    ]
    resources = ["${aws_s3_bucket.data.arn}/${var.raw_prefix}*"]
  }

  statement {
    actions   = ["secretsmanager:GetSecretValue"]
    resources = [aws_secretsmanager_secret.ncbi_credentials.arn]
  }

  statement {
    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]
    resources = ["*"]
  }
}

resource "aws_iam_role_policy" "pubmed_ingest" {
  name   = "${var.rag_api_name}-ingest-policy"
  role   = aws_iam_role.pubmed_ingest.id
  policy = data.aws_iam_policy_document.pubmed_ingest_policy.json
}

resource "aws_lambda_function" "pubmed_ingest" {
  function_name = "${var.rag_api_name}-ingest"
  role          = aws_iam_role.pubmed_ingest.arn
  handler       = "lambda_ingest_handler.handler"
  runtime       = "python3.11"
  timeout       = 900
  memory_size   = 1024

  filename         = data.archive_file.pubmed_ingest_lambda.output_path
  source_code_hash = data.archive_file.pubmed_ingest_lambda.output_base64sha256

  environment {
    variables = {
      NCBI_SECRET_ARN = aws_secretsmanager_secret.ncbi_credentials.arn
      S3_BUCKET       = aws_s3_bucket.data.bucket
      RAW_PREFIX      = var.raw_prefix
      PUBMED_QUERY    = var.pubmed_query
      RETMAX          = var.pubmed_retmax
      BATCH_SIZE      = var.pubmed_batch_size
    }
  }

  tags = var.tags
}

resource "aws_cloudwatch_log_group" "pubmed_ingest" {
  name              = "/aws/lambda/${aws_lambda_function.pubmed_ingest.function_name}"
  retention_in_days = 14
  tags              = var.tags
}
