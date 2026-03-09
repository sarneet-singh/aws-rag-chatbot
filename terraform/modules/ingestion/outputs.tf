output "lambda_role_arn" {
  value = aws_iam_role.lambda.arn
}

output "state_machine_arn" {
  value = aws_sfn_state_machine.ingestion.arn
}
