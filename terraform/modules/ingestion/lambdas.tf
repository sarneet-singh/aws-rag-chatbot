data "archive_file" "scraper" {
  type        = "zip"
  source_dir  = "${path.module}/builds/package"
  output_path = "${path.module}/builds/scraper.zip"
}

data "archive_file" "chunker" {
  type        = "zip"
  source_dir  = "${path.module}/builds/package"
  output_path = "${path.module}/builds/chunker.zip"
}

data "archive_file" "embedder" {
  type        = "zip"
  source_dir  = "${path.module}/builds/package"
  output_path = "${path.module}/builds/embedder.zip"
}

resource "aws_s3_bucket" "artifacts" {
  bucket = "${var.project_name}-ingest-artifacts"
}

resource "aws_s3_object" "scraper" {
  bucket = aws_s3_bucket.artifacts.id
  key    = "scraper.zip"
  source = data.archive_file.scraper.output_path
  etag   = data.archive_file.scraper.output_md5
}

resource "aws_s3_object" "chunker" {
  bucket = aws_s3_bucket.artifacts.id
  key    = "chunker.zip"
  source = data.archive_file.chunker.output_path
  etag   = data.archive_file.chunker.output_md5
}

resource "aws_s3_object" "embedder" {
  bucket = aws_s3_bucket.artifacts.id
  key    = "embedder.zip"
  source = data.archive_file.embedder.output_path
  etag   = data.archive_file.embedder.output_md5
}

resource "aws_s3_bucket" "raw" {
  bucket = "${var.project_name}-raw-docs"
}

resource "aws_s3_bucket_versioning" "raw" {
  bucket = aws_s3_bucket.raw.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "raw" {
  bucket = aws_s3_bucket.raw.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "raw" {
  bucket = aws_s3_bucket.raw.id
  rule {
    id     = "expire-after-90-days"
    status = "Enabled"
    filter {}
    expiration {
      days = 90
    }
  }
}

resource "aws_s3_bucket" "chunks" {
  bucket = "${var.project_name}-chunks"
}

resource "aws_s3_bucket_versioning" "chunks" {
  bucket = aws_s3_bucket.chunks.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "chunks" {
  bucket = aws_s3_bucket.chunks.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "chunks" {
  bucket = aws_s3_bucket.chunks.id
  rule {
    id     = "expire-after-90-days"
    status = "Enabled"
    filter {}
    expiration {
      days = 90
    }
  }
}

resource "aws_lambda_function" "scraper" {
  function_name    = "${var.project_name}-scraper"
  role             = aws_iam_role.lambda.arn
  handler          = "scraper.handler"
  runtime          = "python3.12"
  timeout          = 600
  memory_size      = 512
  s3_bucket        = aws_s3_object.scraper.bucket
  s3_key           = aws_s3_object.scraper.key
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
  s3_bucket        = aws_s3_object.chunker.bucket
  s3_key           = aws_s3_object.chunker.key
  source_code_hash = data.archive_file.chunker.output_base64sha256
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
  s3_bucket        = aws_s3_object.embedder.bucket
  s3_key           = aws_s3_object.embedder.key
  source_code_hash = data.archive_file.embedder.output_base64sha256
  environment {
    variables = {
      CHUNKS_BUCKET             = aws_s3_bucket.chunks.bucket
      PINECONE_INDEX_NAME       = var.pinecone_index_name
      PINECONE_API_KEY_SSM_PATH = var.pinecone_api_key_ssm_path
      OPENAI_API_KEY_SSM_PATH   = var.openai_api_key_ssm_path
    }
  }
}
