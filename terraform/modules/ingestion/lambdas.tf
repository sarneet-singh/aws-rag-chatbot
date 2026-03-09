data "archive_file" "scraper" {
  type        = "zip"
  source_dir  = "${path.root}/../../src/ingestion"
  output_path = "${path.module}/builds/scraper.zip"
}

resource "aws_s3_bucket" "raw" {
  bucket = "${var.project_name}-raw-docs"
}

resource "aws_s3_bucket" "chunks" {
  bucket = "${var.project_name}-chunks"
}

resource "aws_lambda_function" "scraper" {
  function_name    = "${var.project_name}-scraper"
  role             = aws_iam_role.lambda.arn
  handler          = "scraper.handler"
  runtime          = "python3.12"
  timeout          = 600
  memory_size      = 512
  filename         = data.archive_file.scraper.output_path
  source_code_hash = data.archive_file.scraper.output_base64sha256
  environment {
    variables = { RAW_BUCKET = aws_s3_bucket.raw.bucket }
  }
}

resource "aws_lambda_function" "chunker" {
  function_name    = "${var.project_name}-chunker"
  role             = aws_iam_role.lambda.arn
  handler          = "chunker.handler"
  runtime          = "python3.12"
  timeout          = 300
  memory_size      = 256
  filename         = data.archive_file.scraper.output_path
  source_code_hash = data.archive_file.scraper.output_base64sha256
  environment {
    variables = { RAW_BUCKET = aws_s3_bucket.raw.bucket, CHUNKS_BUCKET = aws_s3_bucket.chunks.bucket }
  }
}

resource "aws_lambda_function" "embedder" {
  function_name    = "${var.project_name}-embedder"
  role             = aws_iam_role.lambda.arn
  handler          = "embedder.handler"
  runtime          = "python3.12"
  timeout          = 600
  memory_size      = 512
  filename         = data.archive_file.scraper.output_path
  source_code_hash = data.archive_file.scraper.output_base64sha256
  environment {
    variables = {
      CHUNKS_BUCKET             = aws_s3_bucket.chunks.bucket
      PINECONE_INDEX_NAME       = var.pinecone_index_name
      PINECONE_API_KEY_SSM_PATH = var.pinecone_api_key_ssm_path
      OPENAI_API_KEY_SSM_PATH   = var.openai_api_key_ssm_path
    }
  }
}
