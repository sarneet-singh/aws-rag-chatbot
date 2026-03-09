module "secrets" {
  source           = "./modules/secrets"
  project_name     = var.project_name
}

module "frontend" {
  source       = "./modules/frontend"
  project_name = var.project_name
}

module "auth" {
  source            = "./modules/auth"
  project_name      = var.project_name
  aws_region        = var.aws_region
  cloudfront_domain = module.frontend.cloudfront_domain
}

module "monitoring" {
  source             = "./modules/monitoring"
  project_name       = var.project_name
  ingestion_role_arn = module.ingestion.lambda_role_arn
}

module "ingestion" {
  source                    = "./modules/ingestion"
  project_name              = var.project_name
  aws_region                = var.aws_region
  pinecone_index_name       = var.pinecone_index_name
  openai_api_key_ssm_path   = module.secrets.openai_api_key_path
  pinecone_api_key_ssm_path = module.secrets.pinecone_api_key_path
  alert_topic_arn           = module.monitoring.alert_topic_arn
}

module "query_api" {
  source                    = "./modules/query-api"
  project_name              = var.project_name
  aws_region                = var.aws_region
  cloudfront_domain         = module.frontend.cloudfront_domain
  cognito_user_pool_id      = module.auth.user_pool_id
  cognito_client_id         = module.auth.client_id
  pinecone_index_name       = var.pinecone_index_name
  openai_api_key_ssm_path   = module.secrets.openai_api_key_path
  pinecone_api_key_ssm_path = module.secrets.pinecone_api_key_path
}
