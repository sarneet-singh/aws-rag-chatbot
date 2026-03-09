module "secrets" {
  source           = "./modules/secrets"
  project_name     = var.project_name
  openai_api_key   = var.openai_api_key
  pinecone_api_key = var.pinecone_api_key
}

module "ingestion" {
  source                  = "./modules/ingestion"
  project_name            = var.project_name
  aws_region              = var.aws_region
  pinecone_index_name     = var.pinecone_index_name
  openai_api_key_ssm_path = module.secrets.openai_api_key_path
  pinecone_api_key_ssm_path = module.secrets.pinecone_api_key_path
}

module "monitoring" {
  source             = "./modules/monitoring"
  project_name       = var.project_name
  ingestion_role_arn = module.ingestion.lambda_role_arn
}
