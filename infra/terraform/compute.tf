data "aws_iam_policy_document" "lambda_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_lambda_function" "backend" {
  function_name    = "${local.name_prefix}-backend"
  role             = aws_iam_role.backend_lambda.arn
  runtime          = "python3.12"
  handler          = "hexarag_api.handler.handler"
  filename         = "backend.zip"
  source_code_hash = filebase64sha256("backend.zip")
  timeout          = 30

  environment {
    variables = {
      RUNTIME_MODE                  = "aws"
      ALLOWED_ORIGINS               = join(",", ["http://localhost:5173", "https://${aws_cloudfront_distribution.frontend.domain_name}"])
      DATABASE_URL                  = "postgresql://hexarag:${var.database_password}@${aws_db_instance.postgres.address}:5432/hexarag"
      SESSION_TABLE_NAME            = aws_dynamodb_table.sessions.name
      MONITORING_BASE_URL           = aws_apigatewayv2_stage.monitoring.invoke_url
      KNOWLEDGE_BASE_ID             = var.knowledge_base_id
      KNOWLEDGE_BASE_DATA_SOURCE_ID = var.knowledge_base_data_source_id
      AGENT_ID                      = var.agent_id
      AGENT_ALIAS_ID                = var.agent_alias_id
    }
  }
}

resource "aws_lambda_function" "monitoring" {
  function_name    = "${local.name_prefix}-monitoring"
  role             = aws_iam_role.monitoring_lambda.arn
  runtime          = "python3.12"
  handler          = "monitoring_api.main.handler"
  filename         = "monitoring.zip"
  source_code_hash = filebase64sha256("monitoring.zip")
  timeout          = 15
}

resource "aws_apigatewayv2_api" "backend" {
  name          = "${local.name_prefix}-backend-api"
  protocol_type = "HTTP"

  cors_configuration {
    allow_credentials = true
    allow_headers     = ["content-type"]
    allow_methods     = ["OPTIONS", "POST"]
    allow_origins     = ["https://${aws_cloudfront_distribution.frontend.domain_name}"]
    max_age           = 300
  }
}

resource "aws_apigatewayv2_integration" "backend" {
  api_id                 = aws_apigatewayv2_api.backend.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.backend.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "backend_chat" {
  api_id    = aws_apigatewayv2_api.backend.id
  route_key = "POST /chat"
  target    = "integrations/${aws_apigatewayv2_integration.backend.id}"
}

resource "aws_apigatewayv2_stage" "backend" {
  api_id      = aws_apigatewayv2_api.backend.id
  name        = "$default"
  auto_deploy = true
}

resource "aws_apigatewayv2_api" "monitoring" {
  name          = "${local.name_prefix}-monitoring-api"
  protocol_type = "HTTP"
}

resource "aws_apigatewayv2_integration" "monitoring" {
  api_id                 = aws_apigatewayv2_api.monitoring.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.monitoring.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "monitoring_metrics" {
  api_id    = aws_apigatewayv2_api.monitoring.id
  route_key = "GET /metrics/{service_name}"
  target    = "integrations/${aws_apigatewayv2_integration.monitoring.id}"
}

resource "aws_apigatewayv2_route" "monitoring_services" {
  api_id    = aws_apigatewayv2_api.monitoring.id
  route_key = "GET /services"
  target    = "integrations/${aws_apigatewayv2_integration.monitoring.id}"
}

resource "aws_apigatewayv2_stage" "monitoring" {
  api_id      = aws_apigatewayv2_api.monitoring.id
  name        = "$default"
  auto_deploy = true
}

resource "aws_lambda_permission" "backend_apigw" {
  statement_id  = "AllowBackendInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.backend.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.backend.execution_arn}/*/*"
}

resource "aws_lambda_permission" "monitoring_apigw" {
  statement_id  = "AllowMonitoringInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.monitoring.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.monitoring.execution_arn}/*/*"
}
