output "backend_api_url" {
  value = aws_apigatewayv2_stage.backend.invoke_url
}

output "monitoring_api_url" {
  value = aws_apigatewayv2_stage.monitoring.invoke_url
}

output "frontend_bucket_name" {
  value = aws_s3_bucket.frontend.bucket
}

output "knowledge_base_bucket_name" {
  value = aws_s3_bucket.knowledge_base.bucket
}

output "session_table_name" {
  value = aws_dynamodb_table.sessions.name
}

output "postgres_endpoint" {
  value = aws_db_instance.postgres.address
}
