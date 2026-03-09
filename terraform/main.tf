module "ingestion" {
  source       = "./modules/ingestion"
  project_name = var.project_name
  aws_region   = var.aws_region
}

module "monitoring" {
  source             = "./modules/monitoring"
  project_name       = var.project_name
  ingestion_role_arn = module.ingestion.lambda_role_arn
}
