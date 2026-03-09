resource "aws_ssm_parameter" "openai_api_key" {
  name  = "/${var.project_name}/openai_api_key"
  type  = "SecureString"
  value = var.openai_api_key
}

resource "aws_ssm_parameter" "pinecone_api_key" {
  name  = "/${var.project_name}/pinecone_api_key"
  type  = "SecureString"
  value = var.pinecone_api_key
}

output "openai_api_key_path" {
  value = aws_ssm_parameter.openai_api_key.name
}

output "pinecone_api_key_path" {
  value = aws_ssm_parameter.pinecone_api_key.name
}
