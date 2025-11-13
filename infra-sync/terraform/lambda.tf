resource "aws_iam_role" "lambda_role" {
  name               = "${local.project_name}-lambda-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
  tags               = local.common_tags
}

data "aws_iam_policy_document" "lambda_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

data "aws_iam_policy_document" "lambda_policy" {
  statement {
    sid    = "AllowSecretsManagerAccess"
    effect = "Allow"

    actions = [
      "secretsmanager:GetSecretValue"
    ]

    resources = [
      var.slack_webhook_secret_arn,
      var.terraform_api_token_secret_arn
    ]
  }

  statement {
    sid    = "AllowDynamoDbAccess"
    effect = "Allow"

    actions = [
      "dynamodb:PutItem",
      "dynamodb:UpdateItem",
      "dynamodb:GetItem",
      "dynamodb:Query",
      "dynamodb:DescribeTable"
    ]

    resources = [aws_dynamodb_table.drift_history.arn]
  }

  statement {
    sid    = "AllowTerraformOperations"
    effect = "Allow"

    actions = [
      "events:PutEvents",
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents"
    ]

    resources = ["*"]
  }
}

resource "aws_iam_policy" "lambda_policy" {
  name   = "${local.project_name}-lambda-policy"
  policy = data.aws_iam_policy_document.lambda_policy.json
  tags   = local.common_tags
}

resource "aws_iam_role_policy_attachment" "lambda_attach" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = aws_iam_policy.lambda_policy.arn
}

resource "aws_cloudwatch_log_group" "drift_detector" {
  name              = "/aws/lambda/${local.lambda_function_name}"
  retention_in_days = 30
  tags              = local.common_tags
}

resource "aws_lambda_function" "drift_detector" {
  function_name = local.lambda_function_name
  role          = aws_iam_role.lambda_role.arn
  handler       = "drift_detector.lambda_handler"
  runtime       = "python3.11"

  filename         = data.archive_file.drift_detector_package.output_path
  source_code_hash = data.archive_file.drift_detector_package.output_base64sha256

  timeout     = var.lambda_timeout
  memory_size = var.lambda_memory_size

  environment {
    variables = {
      TERRAFORM_ORG_NAME              = var.terraform_org_name
      TERRAFORM_WORKSPACE             = var.terraform_workspace
      TERRAFORM_API_TOKEN_SECRET_ARN  = var.terraform_api_token_secret_arn
      SLACK_WEBHOOK_SECRET_ARN        = var.slack_webhook_secret_arn
      AUTO_REMEDIATE                  = var.auto_remediate ? "true" : "false"
      DRIFT_HISTORY_TABLE_NAME        = aws_dynamodb_table.drift_history.name
    }
  }

  depends_on = [
    aws_cloudwatch_log_group.drift_detector,
    aws_iam_role_policy_attachment.lambda_attach
  ]

  tags = local.common_tags
}

