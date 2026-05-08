variable "aws_region" {
  type = string
}

variable "project_name" {
  type = string
}

variable "environment" {
  type = string
}

variable "database_password" {
  type      = string
  sensitive = true
}

variable "agent_id" {
  type = string
}

variable "agent_alias_id" {
  type = string
}

variable "knowledge_base_id" {
  type = string
}

variable "knowledge_base_data_source_id" {
  type = string
}
