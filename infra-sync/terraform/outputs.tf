output "lambda_function_name" {
  description = "Name of the drift detector Lambda function."
  value       = aws_lambda_function.drift_detector.function_name
}

output "dynamodb_table_name" {
  description = "Name of the drift history DynamoDB table."
  value       = aws_dynamodb_table.drift_history.name
}

output "eventbridge_rule_arn" {
  description = "ARN of the EventBridge rule monitoring AWS resource changes."
  value       = aws_cloudwatch_event_rule.resource_change.arn
}

