data "aws_iam_policy_document" "backend_lambda" {
  statement {
    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]
    resources = ["arn:aws:logs:*:*:*"]
  }

  statement {
    actions = [
      "dynamodb:GetItem",
      "dynamodb:PutItem",
    ]
    resources = [aws_dynamodb_table.sessions.arn]
  }

  statement {
    actions = [
      "s3:GetObject",
      "s3:ListBucket",
    ]
    resources = [
      aws_s3_bucket.knowledge_base.arn,
      "${aws_s3_bucket.knowledge_base.arn}/*",
    ]
  }

  statement {
    actions = [
      "bedrock:InvokeAgent",
      "bedrock:StartIngestionJob",
    ]
    resources = ["*"]
  }
}

resource "aws_iam_role" "backend_lambda" {
  name               = "${local.name_prefix}-backend-lambda"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
}

resource "aws_iam_role_policy" "backend_lambda" {
  name   = "${local.name_prefix}-backend-lambda"
  role   = aws_iam_role.backend_lambda.id
  policy = data.aws_iam_policy_document.backend_lambda.json
}

resource "aws_iam_role" "monitoring_lambda" {
  name               = "${local.name_prefix}-monitoring-lambda"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
}

resource "aws_iam_role_policy_attachment" "monitoring_logs" {
  role       = aws_iam_role.monitoring_lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role" "sync_lambda" {
  name               = "${local.name_prefix}-sync-lambda"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
}

resource "aws_iam_role_policy" "sync_lambda" {
  name = "${local.name_prefix}-sync-lambda"
  role = aws_iam_role.sync_lambda.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "bedrock:StartIngestionJob",
          "s3:GetObject",
          "s3:ListBucket",
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role" "sync_scheduler" {
  name = "${local.name_prefix}-sync-scheduler"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = "sts:AssumeRole"
        Principal = {
          Service = "scheduler.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy" "sync_scheduler" {
  name = "${local.name_prefix}-sync-scheduler"
  role = aws_iam_role.sync_scheduler.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "lambda:InvokeFunction",
        ]
        Resource = aws_lambda_function.kb_sync.arn
      }
    ]
  })
}
