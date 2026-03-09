data "archive_file" "query" {
  type        = "zip"
  source_dir  = "${path.root}/../../src/query"
  output_path = "${path.module}/builds/query.zip"
}

resource "aws_iam_role" "lambda" {
  name               = "${var.project_name}-query-lambda"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Action    = "sts:AssumeRole"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy" "lambda_policy" {
  role = aws_iam_role.lambda.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      { Effect = "Allow", Action = ["dynamodb:PutItem", "dynamodb:GetItem", "dynamodb:Query"], Resource = [aws_dynamodb_table.sessions.arn, aws_dynamodb_table.feedback.arn] },
      { Effect = "Allow", Action = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"], Resource = "*" },
      { Effect = "Allow", Action = ["ssm:GetParameter"], Resource = "arn:aws:ssm:*:*:parameter/${var.project_name}/*" },
    ]
  })
}

resource "aws_lambda_function" "rag" {
  function_name    = "${var.project_name}-rag"
  role             = aws_iam_role.lambda.arn
  handler          = "rag.handler"
  runtime          = "python3.12"
  timeout          = 60
  memory_size      = 512
  filename         = data.archive_file.query.output_path
  source_code_hash = data.archive_file.query.output_base64sha256
  environment {
    variables = {
      PINECONE_INDEX_NAME       = var.pinecone_index_name
      PINECONE_API_KEY_SSM_PATH = var.pinecone_api_key_ssm_path
      OPENAI_API_KEY_SSM_PATH   = var.openai_api_key_ssm_path
      DYNAMODB_SESSIONS_TABLE   = aws_dynamodb_table.sessions.name
      DYNAMODB_FEEDBACK_TABLE   = aws_dynamodb_table.feedback.name
    }
  }
}

resource "aws_lambda_function" "feedback" {
  function_name    = "${var.project_name}-feedback"
  role             = aws_iam_role.lambda.arn
  handler          = "rag.feedback_handler"
  runtime          = "python3.12"
  timeout          = 30
  memory_size      = 256
  filename         = data.archive_file.query.output_path
  source_code_hash = data.archive_file.query.output_base64sha256
  environment {
    variables = {
      PINECONE_INDEX_NAME       = var.pinecone_index_name
      PINECONE_API_KEY_SSM_PATH = var.pinecone_api_key_ssm_path
      OPENAI_API_KEY_SSM_PATH   = var.openai_api_key_ssm_path
      DYNAMODB_SESSIONS_TABLE   = aws_dynamodb_table.sessions.name
      DYNAMODB_FEEDBACK_TABLE   = aws_dynamodb_table.feedback.name
    }
  }
}

resource "aws_lambda_permission" "rag" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.rag.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.main.execution_arn}/*/*"
}

resource "aws_lambda_permission" "feedback" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.feedback.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.main.execution_arn}/*/*"
}
