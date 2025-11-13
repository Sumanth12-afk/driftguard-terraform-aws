resource "aws_cloudwatch_event_rule" "resource_change" {
  name        = "${local.project_name}-resource-change"
  description = "Capture AWS resource configuration changes for drift detection."

  event_pattern = jsonencode({
    source = [
      "aws.ec2",
      "aws.s3",
      "aws.iam"
    ]
    detail-type = [
      "AWS API Call via CloudTrail"
    ]
    detail = {
      eventSource = [
        "ec2.amazonaws.com",
        "s3.amazonaws.com",
        "iam.amazonaws.com"
      ]
      eventName = [
        "RunInstances",
        "TerminateInstances",
        "ModifyInstanceAttribute",
        "PutBucketPolicy",
        "DeleteBucketPolicy",
        "PutBucketVersioning",
        "DeleteBucket",
        "CreateUser",
        "PutUserPolicy",
        "DeleteUserPolicy",
        "AttachRolePolicy",
        "DetachRolePolicy",
        "CreateRole",
        "DeleteRole"
      ]
    }
  })

  tags = local.common_tags
}

resource "aws_cloudwatch_event_target" "lambda" {
  rule      = aws_cloudwatch_event_rule.resource_change.name
  target_id = "DriftDetectorLambda"
  arn       = aws_lambda_function.drift_detector.arn
}

resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.drift_detector.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.resource_change.arn
}

