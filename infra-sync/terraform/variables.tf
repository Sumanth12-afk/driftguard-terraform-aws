variable "aws_region" {
  description = "AWS region for all resources."
  type        = string
  default     = "ap-south-1"
}

variable "project_name" {
  description = "Friendly name used for tagging."
  type        = string
  default     = "infra-sync-drift-guard"
}

variable "environment" {
  description = "Deployment environment (e.g., dev, prod)."
  type        = string
  default     = "prod"
}

variable "lambda_timeout" {
  description = "Timeout for the drift detector Lambda function."
  type        = number
  default     = 60
}

variable "lambda_memory_size" {
  description = "Memory size for the drift detector Lambda function."
  type        = number
  default     = 512
}

variable "dynamodb_point_in_time_recovery" {
  description = "Enable point-in-time recovery for the drift history table."
  type        = bool
  default     = true
}

variable "auto_remediate" {
  description = "Flag to enable automatic remediation via Terraform Cloud apply."
  type        = bool
  default     = false
}

variable "terraform_org_name" {
  description = "Terraform Cloud organization name."
  type        = string
}

variable "terraform_workspace" {
  description = "Terraform Cloud workspace to query for drift detection."
  type        = string
}

variable "slack_webhook_secret_arn" {
  description = "ARN of the AWS Secrets Manager secret storing the Slack webhook URL."
  type        = string
}

variable "terraform_api_token_secret_arn" {
  description = "ARN of the AWS Secrets Manager secret storing the Terraform Cloud API token."
  type        = string
}

variable "create_cloudtrail" {
  description = "When true, deploy a CloudTrail trail for management events feeding EventBridge."
  type        = bool
  default     = true
}

variable "create_test_ec2" {
  description = "When true, provision a sample EC2 instance for drift testing."
  type        = bool
  default     = false
}

variable "ec2_instance_type" {
  description = "Instance type for the optional test EC2 instance."
  type        = string
  default     = "t3.micro"
}

variable "ec2_key_name" {
  description = "Optional EC2 key pair name to associate with the instance."
  type        = string
  default     = null
}

variable "ec2_subnet_id" {
  description = "Subnet ID for the optional test EC2 instance. When null, defaults to the first subnet in the default VPC."
  type        = string
  default     = null
}

variable "ec2_additional_tags" {
  description = "Additional tags to attach to the sample EC2 instance."
  type        = map(string)
  default     = {}
}

