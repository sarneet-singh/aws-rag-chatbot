variable "project_name" {}
variable "aws_region" {}
variable "cloudfront_domain" {}
variable "cognito_user_pool_id" {}
variable "cognito_client_id" {}

variable "pinecone_index_name" { default = "aws-rag" }
variable "openai_api_key_ssm_path" {}
variable "pinecone_api_key_ssm_path" {}
