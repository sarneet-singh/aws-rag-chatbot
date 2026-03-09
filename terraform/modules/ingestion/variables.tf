variable "project_name" {}
variable "aws_region" {}
variable "pinecone_index_name" { default = "aws-rag" }
variable "alert_topic_arn" { default = "" }
variable "openai_api_key_ssm_path" {}
variable "pinecone_api_key_ssm_path" {}
