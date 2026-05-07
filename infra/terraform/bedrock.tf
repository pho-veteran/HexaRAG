locals {
  knowledge_base_bucket_arn = aws_s3_bucket.knowledge_base.arn
}

resource "aws_ssm_parameter" "knowledge_base_id" {
  name  = "/${local.name_prefix}/knowledge_base_id"
  type  = "String"
  value = var.knowledge_base_id
}

resource "aws_ssm_parameter" "knowledge_base_data_source_id" {
  name  = "/${local.name_prefix}/knowledge_base_data_source_id"
  type  = "String"
  value = var.knowledge_base_data_source_id
}

resource "aws_ssm_parameter" "agent_runtime_arn" {
  name  = "/${local.name_prefix}/agent_runtime_arn"
  type  = "String"
  value = var.agent_runtime_arn
}
