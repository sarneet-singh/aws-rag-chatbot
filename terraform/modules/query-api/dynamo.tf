resource "aws_dynamodb_table" "sessions" {
  name         = "${var.project_name}-sessions"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "session_id"
  range_key    = "timestamp"

  attribute {
    name = "session_id"
    type = "S"
  }
  attribute {
    name = "timestamp"
    type = "S"
  }

  point_in_time_recovery {
    enabled = true
  }
}

resource "aws_dynamodb_table" "feedback" {
  name         = "${var.project_name}-feedback"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "session_id"
  range_key    = "message_id"

  attribute {
    name = "session_id"
    type = "S"
  }
  attribute {
    name = "message_id"
    type = "S"
  }

  point_in_time_recovery {
    enabled = true
  }
}
