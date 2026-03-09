data "aws_ssm_parameter" "openai_api_key" {
  name = "/${var.project_name}/openai_api_key"
}

data "aws_ssm_parameter" "pinecone_api_key" {
  name = "/${var.project_name}/pinecone_api_key"
}

output "openai_api_key_path" {
  value = data.aws_ssm_parameter.openai_api_key.name
}

output "pinecone_api_key_path" {
  value = data.aws_ssm_parameter.pinecone_api_key.name
}
