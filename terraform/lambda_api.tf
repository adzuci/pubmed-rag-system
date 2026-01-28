data "archive_file" "rag_lambda" {
  type        = "zip"
  source_file = "${path.module}/../api/lambda_handler.py"
  output_path = "${path.module}/rag_lambda.zip"
}

data "aws_iam_policy_document" "rag_lambda_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "rag_lambda" {
  name               = "${var.rag_api_name}-lambda-role"
  assume_role_policy = data.aws_iam_policy_document.rag_lambda_assume.json
  tags               = var.tags
}

data "aws_iam_policy_document" "rag_lambda_policy" {
  statement {
    actions = [
      "bedrock-agent-runtime:Retrieve",
      "bedrock-agent-runtime:RetrieveAndGenerate",
      "bedrock:InvokeModel",
      "bedrock:Retrieve",
      "bedrock:RetrieveAndGenerate",
    ]
    resources = ["*"]
  }

  statement {
    actions = [
      "aws-marketplace:ViewSubscriptions",
      "aws-marketplace:Subscribe",
    ]
    resources = ["*"]
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

resource "aws_iam_role_policy" "rag_lambda" {
  name   = "${var.rag_api_name}-lambda-policy"
  role   = aws_iam_role.rag_lambda.id
  policy = data.aws_iam_policy_document.rag_lambda_policy.json
}

resource "aws_lambda_function" "rag_query" {
  function_name = "${var.rag_api_name}-query"
  role          = aws_iam_role.rag_lambda.arn
  handler       = "lambda_handler.handler"
  runtime       = "python3.11"
  timeout       = 30
  memory_size   = 512

  filename         = data.archive_file.rag_lambda.output_path
  source_code_hash = data.archive_file.rag_lambda.output_base64sha256

  environment {
    variables = {
      BEDROCK_KB_ID     = module.bedrock.default_kb_identifier
      BEDROCK_MODEL_ARN = var.bedrock_model_arn
    }
  }

  tags = var.tags
}

resource "aws_apigatewayv2_api" "rag_api" {
  name          = var.rag_api_name
  protocol_type = "HTTP"

  cors_configuration {
    allow_headers = ["Content-Type", "Authorization"]
    allow_methods = ["POST", "OPTIONS"]
    allow_origins = ["*"]
  }

  tags = var.tags
}

resource "aws_apigatewayv2_integration" "rag_api" {
  api_id                 = aws_apigatewayv2_api.rag_api.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.rag_query.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "rag_query" {
  api_id    = aws_apigatewayv2_api.rag_api.id
  route_key = "POST /query"
  target    = "integrations/${aws_apigatewayv2_integration.rag_api.id}"
}

resource "aws_apigatewayv2_stage" "rag_api" {
  api_id      = aws_apigatewayv2_api.rag_api.id
  name        = "$default"
  auto_deploy = true
  tags        = var.tags
}

resource "aws_lambda_permission" "rag_api" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.rag_query.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.rag_api.execution_arn}/*/*"
}
