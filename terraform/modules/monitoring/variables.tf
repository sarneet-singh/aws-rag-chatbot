variable "project_name" {}
variable "ingestion_role_arn" {}
variable "alert_topic_arn" {
  description = "SNS topic ARN for alerts (output from this module)"
  default     = ""
}
