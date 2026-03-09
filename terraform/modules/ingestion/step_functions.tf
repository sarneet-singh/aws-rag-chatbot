resource "aws_sfn_state_machine" "ingestion" {
  name     = "${var.project_name}-ingestion"
  role_arn = aws_iam_role.sfn.arn
  definition = jsonencode({
    Comment = "RAG ingestion pipeline"
    StartAt = "Scrape"
    States = {
      Scrape = {
        Type       = "Task"
        Resource   = aws_lambda_function.scraper.arn
        ResultPath = "$.scrape_result"
        Next       = "Chunk"
        Catch      = [{ ErrorEquals = ["States.ALL"], Next = "NotifyFailure", ResultPath = "$.error" }]
        Retry      = [{ ErrorEquals = ["States.TaskFailed"], IntervalSeconds = 30, MaxAttempts = 2 }]
      }
      Chunk = {
        Type       = "Task"
        Resource   = aws_lambda_function.chunker.arn
        Parameters = { "run_prefix.$" = "$.scrape_result.run_prefix" }
        ResultPath = "$.chunk_result"
        Next       = "Embed"
        Catch      = [{ ErrorEquals = ["States.ALL"], Next = "NotifyFailure", ResultPath = "$.error" }]
        Retry      = [{ ErrorEquals = ["States.TaskFailed"], IntervalSeconds = 30, MaxAttempts = 2 }]
      }
      Embed = {
        Type       = "Task"
        Resource   = aws_lambda_function.embedder.arn
        Parameters = { "run_prefix.$" = "$.chunk_result.run_prefix" }
        ResultPath = "$.embed_result"
        End        = true
        Catch      = [{ ErrorEquals = ["States.ALL"], Next = "NotifyFailure", ResultPath = "$.error" }]
        Retry      = [{ ErrorEquals = ["States.TaskFailed"], IntervalSeconds = 60, MaxAttempts = 2 }]
      }
      NotifyFailure = {
        Type     = "Task"
        Resource = "arn:aws:states:::sns:publish"
        Parameters = {
          TopicArn  = var.alert_topic_arn
          "Message.$" = "States.Format('Ingestion pipeline failed: {}', $.error)"
          Subject   = "RAG Ingestion Failure"
        }
        End = true
      }
    }
  })
}
