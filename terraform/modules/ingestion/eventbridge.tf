resource "aws_cloudwatch_event_rule" "weekly" {
  name                = "${var.project_name}-weekly-ingestion"
  schedule_expression = "cron(0 2 ? * MON *)" # Every Monday at 2am UTC
}

resource "aws_cloudwatch_event_target" "sfn" {
  rule     = aws_cloudwatch_event_rule.weekly.name
  arn      = aws_sfn_state_machine.ingestion.arn
  role_arn = aws_iam_role.sfn.arn
}
