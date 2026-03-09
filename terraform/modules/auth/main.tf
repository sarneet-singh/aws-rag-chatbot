resource "aws_cognito_user_pool" "main" {
  name = "${var.project_name}-users"
  password_policy {
    minimum_length    = 8
    require_uppercase = true
    require_numbers   = true
  }
  auto_verified_attributes = ["email"]
}

resource "aws_cognito_user_pool_client" "web" {
  name                                 = "${var.project_name}-web"
  user_pool_id                         = aws_cognito_user_pool.main.id
  generate_secret                      = false
  allowed_oauth_flows                  = ["code"]
  allowed_oauth_scopes                 = ["email", "openid", "profile"]
  callback_urls                        = ["https://${var.cloudfront_domain}/callback"]
  logout_urls                          = ["https://${var.cloudfront_domain}"]
  allowed_oauth_flows_user_pool_client = true
  supported_identity_providers         = ["COGNITO"]
}

resource "aws_cognito_user_pool_domain" "main" {
  domain       = "${var.project_name}-auth"
  user_pool_id = aws_cognito_user_pool.main.id
}

output "user_pool_id" { value = aws_cognito_user_pool.main.id }
output "client_id" { value = aws_cognito_user_pool_client.web.id }
output "auth_domain" { value = "https://${aws_cognito_user_pool_domain.main.domain}.auth.${var.aws_region}.amazoncognito.com" }
