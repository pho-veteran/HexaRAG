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

resource "aws_ssm_parameter" "agent_id" {
  name  = "/${local.name_prefix}/agent_id"
  type  = "String"
  value = var.agent_id
}

resource "aws_ssm_parameter" "agent_alias_id" {
  name  = "/${local.name_prefix}/agent_alias_id"
  type  = "String"
  value = var.agent_alias_id
}
