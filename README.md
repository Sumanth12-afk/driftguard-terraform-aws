# InfraSync – DriftGuard for AWS

InfraSync DriftGuard is an event-driven automation system that detects, reports, and optionally remediates infrastructure drift for Terraform-managed AWS environments. It listens for configuration changes (EC2, S3, IAM) via Amazon EventBridge, invokes a Python Lambda function to compare live state against Terraform Cloud, posts alerts to Slack, and archives drift history in DynamoDB. Terraform IaC provisions and wires all AWS components. Documentation and partner-ready collateral are included for AWS Partner Central submissions.

---

## Features

- **Real-time drift detection** for EC2, S3, and IAM changes outside Terraform control.
- **Terraform Cloud integration** (runs API) for speculative plans and optional auto-remediation.
- **Slack notifications** summarizing drift events (resource, change type, status, link to plan).
- **DynamoDB history log** with TTL and point-in-time recovery for auditing.
- **Event-driven architecture** built on EventBridge + Lambda with CloudWatch logging.
- **Optional dashboard scaffold** (Next.js/Tailwind) ready to consume DynamoDB data.
- **Partner collateral** – architecture diagram, spec sheet, case study, security guidance.

---

## Architecture

```
AWS EventBridge (CloudTrail events)
        ↓
AWS Lambda drift detector (Python 3.11)
        ↓ (Terraform Cloud Runs API)
Slack notifications + DynamoDB history log
        ↓
Optional Next.js/Tailwind dashboard
```

Secrets (Slack webhook + Terraform token) are stored in AWS Secrets Manager. IAM roles follow least-privilege. CloudTrail is enabled to ensure EventBridge receives configuration change events.

---

## Repository Structure

```
infra-sync/
├── terraform/                   # IaC modules & variables
│   ├── main.tf                  # providers, backend, archive packaging
│   ├── variables.tf             # configurable inputs
│   ├── lambda.tf                # Lambda function + IAM
│   ├── eventbridge.tf           # EventBridge rule & permissions
│   ├── dynamodb.tf              # Drift history table
│   ├── cloudtrail.tf            # CloudTrail + S3 log bucket
│   ├── ec2.tf                   # Optional test EC2 instance
│   ├── outputs.tf
│   └── terraform.tfvars.example
├── lambda/                      # Python Lambda package
│   ├── drift_detector.py
│   ├── terraform_api.py
│   ├── slack_notifier.py
│   └── dynamodb_logger.py
├── docs/                        # Partner documentation
│   ├── architecture.png
│   ├── case-study.pdf
│   ├── specification-sheet.pdf
│   └── README.md
├── frontend/                    # Optional Next.js dashboard starter
│   └── README.md
├── dist/                        # Lambda zip artifacts (ignored by git)
├── .gitignore
└── README.md                     # (this file)
```

---

## Prerequisites

- Terraform CLI ≥ 1.13.5 with remote backend access to Terraform Cloud.
- Terraform Cloud organization & workspace (e.g., `before-you-solutions/infra-sync-prod`).
- AWS account with rights to provision EventBridge, Lambda, IAM, DynamoDB, CloudTrail, S3.
- Slack workspace with incoming webhook.
- Python tooling (optional) if you modify Lambda code.

### Secrets in AWS Secrets Manager

Create two secrets in Region `ap-south-1` (adjust if needed):

```bash
# Slack webhook URL
aws secretsmanager create-secret \
  --name infra-sync/slack/webhook \
  --secret-string "https://hooks.slack.com/services/XXX/YYY/ZZZ" \
  --region ap-south-1

# Terraform Cloud API token (user/org token starting with tfe.)
aws secretsmanager create-secret \
  --name infra-sync/terraform/token \
  --secret-string "tfe.your_token_here" \
  --region ap-south-1
```

Record each secret’s ARN; reference them in `terraform.tfvars`.

---

## Configuration

Create `infra-sync/terraform/terraform.tfvars`:

```hcl
aws_region                   = "ap-south-1"
project_name                 = "infra-sync-drift-guard"
environment                  = "prod"
terraform_org_name           = "your_org"
terraform_workspace          = "infra-sync-prod"
slack_webhook_secret_arn     = "arn:aws:secretsmanager:ap-south-1:123456789012:secret:infra-sync/slack/webhook"
terraform_api_token_secret_arn = "arn:aws:secretsmanager:ap-south-1:123456789012:secret:infra-sync/terraform/token"
auto_remediate               = false        # set true to call terraform apply automatically
dynamodb_point_in_time_recovery = true
create_cloudtrail             = true
create_test_ec2              = true         # deploys a sample EC2 instance for drift testing
ec2_instance_type            = "t3.micro"
ec2_key_name                 = null
ec2_subnet_id                = null         # optional override instead of default VPC subnet
ec2_additional_tags = {
  Environment = "test"
}
```

> **Note:** The remote backend is configured inside `main.tf`; Terraform Cloud credentials must be set via CLI login or environment variables.

---

## Deployment

```bash
cd infra-sync/terraform
terraform login                      # if not already logged into Terraform Cloud
terraform init -reconfigure
terraform plan
terraform apply
```

Terraform provisions:
- CloudTrail trail + S3 log bucket.
- EventBridge rule capturing CloudTrail change events.
- Lambda drift detector (Python 3.11) + IAM role/policy.
- DynamoDB drift history table (PITR + TTL).
- Optional EC2 drift-test instance (`create_test_ec2`).
- Slack and Terraform token secret references.

Outputs display Lambda function name, EventBridge ARN, and DynamoDB table.

---

## Operations

1. **Trigger drift** – manually change or terminate the optional EC2 instance (or any Terraform-managed resource). EventBridge emits the event.
2. **Lambda execution** – introduces a speculative plan via Terraform Cloud Runs API.
3. **Notifications & logging** – Slack alert posts to the configured channel, DynamoDB logs the record with status `Detected` or `NoDrift`.
4. **Auto-remediation (optional)** – set `auto_remediate = true` to issue `terraform apply` when drift is detected.

### Monitoring

- CloudWatch Logs: `/aws/lambda/infra-sync-drift-guard-drift-detector`
- DynamoDB table: `infra-sync-drift-guard-drift-history`
- Terraform Cloud runs: workspace `infra-sync-prod` (speculative by default)
- Slack channel: incoming webhook destination

---

## Cleanup

Destroy all provisioned resources via Terraform Cloud or CLI:

```bash
cd infra-sync/terraform
terraform destroy
```

This removes EventBridge rule, Lambda, IAM roles/policies, CloudTrail trail + bucket, DynamoDB table, optional EC2 instance, and CloudWatch log group.

---

## Optional Gmail/SNS Alerts

To supplement Slack notifications with email:

1. Create an SNS topic (e.g., `infra-sync-drift-alerts`) and subscribe your Gmail address.
2. Give the Lambda IAM policy `sns:Publish` to the topic ARN.
3. Update `drift_detector.py` to publish alerts to SNS after Slack notifications.

SNS handles formatting and delivery to email endpoints, avoiding Gmail SMTP rate limits.

---

## Contributing

1. Fork the repository.
2. Create a feature branch: `git checkout -b feature/my-change`.
3. Commit changes and push.
4. Open a pull request describing modifications and testing performed.

---

## Challenges & Lessons Learned

1. **Token rotation broke Lambda access** – Recreating the Terraform Cloud token generated a new Secret Manager ARN, which invalidated the Lambda IAM policy. Updating `terraform_api_token_secret_arn` and reapplying Terraform refreshed permissions.
2. **Missing configuration version in Terraform Cloud** – Lambda runs initially failed with HTTP 422 until a configuration version existed. Running `terraform plan/apply` in the remote workspace seeded the configuration.
3. **HTTP 404 from Terraform API** – Using an insufficient token produced 404 errors on `/runs`. The fix was creating a valid `tfe.` token with access to the workspace and storing it securely.
4. **EventBridge didn’t fire without CloudTrail** – Change events never reached Lambda until CloudTrail was enabled. Provisioning the trail via Terraform ensured CloudTrail forwarded management events.
5. **Archive path for Lambda source** – The remote backend couldn’t zip `../lambda`. Copying the Lambda package under `terraform/` and adjusting `archive_file` fixed the packaging step.
6. **Remote backend networking** – Switching to Terraform Cloud required CLI login and occasionally retrying `terraform destroy` when network timeouts (discovery document fetch) occurred.

---

## License

Apache License 2.0 – see [LICENSE](infra-sync/LICENSE) for full text.

