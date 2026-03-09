variable "project_name" {}
variable "aws_region" {}

variable "openai_api_key" {
  sensitive = true
  default   = ""
}

variable "pinecone_api_key" {
  sensitive = true
  default   = ""
}

variable "pinecone_index_name" {
  default = "aws-rag"
}

variable "alert_topic_arn" {
  default = ""
}
