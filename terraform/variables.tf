variable "aws_region" {
  default = "us-east-1"
}

variable "project_name" {
  default = "aws-rag-chatbot"
}

variable "openai_api_key" {
  sensitive = true
}

variable "pinecone_api_key" {
  sensitive = true
}

variable "pinecone_index_name" {
  default = "aws-rag"
}
