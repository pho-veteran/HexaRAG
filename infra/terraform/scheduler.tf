resource "aws_lambda_function" "kb_sync" {
  function_name    = "${local.name_prefix}-kb-sync"
  role             = aws_iam_role.sync_lambda.arn
  runtime          = "python3.12"
  handler          = "sync_knowledge_base.handler"
  filename         = "kb-sync.zip"
  source_code_hash = filebase64sha256("kb-sync.zip")
  timeout          = 60

  environment {
    variables = {
      KNOWLEDGE_BASE_ID             = var.knowledge_base_id
      KNOWLEDGE_BASE_DATA_SOURCE_ID = var.knowledge_base_data_source_id
    }
  }
}

resource "aws_scheduler_schedule" "knowledge_base_sync" {
  name       = "${local.name_prefix}-kb-sync"
  group_name = "default"

  flexible_time_window {
    mode = "OFF"
  }

  schedule_expression = "rate(6 hours)"

  target {
    arn      = aws_lambda_function.kb_sync.arn
    role_arn = aws_iam_role.sync_scheduler.arn
  }
}
