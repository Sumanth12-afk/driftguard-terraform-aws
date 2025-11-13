# InfraSync – DriftGuard for AWS

InfraSync – DriftGuard for AWS is an automation system that detects and remediates infrastructure drift across AWS accounts that are managed with Terraform Cloud. The solution listens for out-of-band AWS configuration changes, validates Terraform state through the Terraform Cloud API, posts detailed alerts to Slack, and records every incident in DynamoDB for audit and analytics. Optional auto-remediation can restore resources back to compliance with Terraform.

## Solution Overview

- **Event-Driven Detection** – AWS EventBridge ingests CloudTrail resource change events for key services (EC2, S3, IAM) and triggers the Drift Detector Lambda function.
- **Terraform State Validation** – The Lambda function calls the Terraform Cloud Runs API to build a speculative plan and checks whether changes exist outside Terraform control.
- **Alerting & Audit** – Slack webhooks receive rich alerts with resource metadata, while DynamoDB keeps a drift history log with TTL and point-in-time recovery.
- **Auto-Remediation (optional)** – When enabled, the Lambda function invokes a Terraform `apply` to realign the infrastructure automatically.
- **Observability & Reporting** – CloudWatch Logs capture traceability, and an optional Next.js dashboard can visualize drift trends from DynamoDB.

```
EventBridge → Lambda Drift Detector → Terraform Cloud → Slack
                                 ↓
                            DynamoDB Log
```

## Repository Structure

```
infra-sync/
├── terraform/                  # IaC for AWS setup
├── lambda/                     # Python Lambda package
├── frontend/                   # Optional Next.js dashboard scaffold
├── docs/                       # AWS Partner collateral
├── dist/                       # Build artifacts (Lambda package)
├── .env.example                # Local development defaults
├── README.md                   # This file
├── SECURITY.md                 # IAM and data protection notes
└── LICENSE                     # Apache-2.0
```

## Prerequisites

- AWS account with permissions to deploy EventBridge, Lambda, DynamoDB, IAM, and Secrets Manager
- Terraform CLI (>= 1.5.0) and Terraform Cloud organization/workspace
- Python 3.11 for local Lambda development
- Slack workspace with incoming webhook

## Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-org/infra-sync-drift-guard.git
   cd infra-sync-drift-guard
   ```

2. **Configure secrets**
   - Store the Slack webhook URL and Terraform Cloud API token in AWS Secrets Manager.
   - Note each secret's ARN; they will be referenced in Terraform inputs.

3. **Populate Terraform variables**
   ```bash
   cd terraform
   cp terraform.tfvars.example terraform.tfvars  # create your own file
   # Update terraform.tfvars with:
   # aws_region, terraform_org_name, terraform_workspace,
   # slack_webhook_secret_arn, terraform_api_token_secret_arn, auto_remediate
   ```

4. **Deploy infrastructure**
   ```bash
   terraform init
   terraform plan
   terraform apply
   ```

5. **Verify deployment**
   - Check the Lambda function `infra-sync-drift-guard-drift-detector` exists.
   - Ensure EventBridge rule `infra-sync-drift-guard-resource-change` is enabled.
   - Confirm DynamoDB table `infra-sync-drift-guard-drift-history` is created.

6. **Simulate drift**
   - Manually alter an EC2 tag, S3 bucket policy, or IAM role outside Terraform.
   - Observe the Slack alert and confirm the entry appears in DynamoDB.

## Lambda Package

The Lambda handler (`lambda/drift_detector.py`) orchestrates Terraform Cloud runs, Slack notifications, and drift logging. Supporting modules include:

- `terraform_api.py` – minimal Terraform Cloud API client for runs, plans, and apply
- `slack_notifier.py` – securely retrieves the webhook secret and posts structured messages
- `dynamodb_logger.py` – records drift events with optional TTL

The Lambda depends only on the AWS SDK (included in the runtime), so no additional packaging steps are required. The Terraform configuration zips the `lambda/` directory into `dist/drift-detector.zip` automatically.

## Optional Dashboard

The `frontend/` directory is reserved for a Next.js + Tailwind CSS dashboard that can query the DynamoDB table (via API Gateway + Lambda or AWS AppSync) to visualize drift history. This component is not implemented by default but the scaffolding is provided for future expansion.

## CI/CD

Add a GitHub Actions workflow to run `terraform fmt`, `terraform plan`, and package/deploy the Lambda using `hashicorp/setup-terraform` and `aws-actions/configure-aws-credentials`. Extend the workflow to run unit tests for Lambda modules and lint checks.

## Environment Variables

| Variable                        | Description                                      |
|---------------------------------|--------------------------------------------------|
| `AWS_REGION`                    | Deployment region                                |
| `TERRAFORM_ORG_NAME`           | Terraform Cloud organization name                |
| `TERRAFORM_WORKSPACE`          | Terraform Cloud workspace                        |
| `TERRAFORM_API_TOKEN_SECRET_ARN` | ARN of Secrets Manager secret storing API token |
| `SLACK_WEBHOOK_SECRET_ARN`     | ARN of Slack webhook secret                      |
| `AUTO_REMEDIATE`               | Enable auto-apply (`true`/`false`)               |
| `DRIFT_HISTORY_TABLE_NAME`     | DynamoDB table name (auto-populated)             |

## Security Considerations

- IAM roles follow least privilege; Lambda accesses only required AWS APIs.
- Secrets are stored in AWS Secrets Manager and retrieved at runtime.
- DynamoDB uses server-side encryption and optional point-in-time recovery.
- CloudWatch Logs capture structured logging for audits.
- To enable auto-remediation, ensure Terraform Cloud workspace permissions and AWS credentials support `terraform apply`.

## Support & Contributions

Issues and feature requests can be submitted via GitHub issues. Contributions are welcome—open a PR with a clear description, tests (if applicable), and adhere to the existing code style.

## License

This project is licensed under the Apache License 2.0. See `LICENSE` for details.

