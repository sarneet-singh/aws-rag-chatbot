output "cloudfront_domain" {
  description = "CloudFront distribution domain name for the frontend"
  value       = module.frontend.cloudfront_domain
}

output "api_endpoint" {
  description = "API Gateway endpoint URL"
  value       = module.query_api.api_endpoint
}

output "cognito_user_pool_id" {
  description = "Cognito User Pool ID"
  value       = module.auth.user_pool_id
}

output "cognito_client_id" {
  description = "Cognito User Pool Client ID"
  value       = module.auth.client_id
}

output "cognito_auth_domain" {
  description = "Cognito hosted UI auth domain"
  value       = module.auth.auth_domain
}

output "state_machine_arn" {
  description = "Step Functions state machine ARN for the ingestion pipeline"
  value       = module.ingestion.state_machine_arn
}
