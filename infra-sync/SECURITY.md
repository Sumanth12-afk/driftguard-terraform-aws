# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| main    | ✅         |

Security fixes are applied to the `main` branch. Forks or older releases should be updated regularly.

## Reporting a Vulnerability

1. Email `security@your-org.com` with the subject `InfraSync DriftGuard Vulnerability`.
2. Include a detailed description, reproduction steps, and any logs or screenshots.
3. Expect an acknowledgment within 48 hours and triage updates within 5 business days.
4. Do not disclose publicly until a fix is released or 90 days have passed, whichever comes first.

## Hardening Guidelines

- Restrict the Lambda execution role to the specific Secrets Manager secrets, DynamoDB table, and CloudWatch Logs resources required.
- Store the Slack webhook URL and Terraform Cloud API token exclusively in AWS Secrets Manager with rotation enabled.
- Enable multi-factor authentication for Terraform Cloud and AWS console access.
- Monitor CloudWatch Logs, EventBridge metrics, and DynamoDB for anomaly detection.
- If auto-remediation is enabled, ensure Terraform Cloud workspaces enforce run tasks or policy checks before apply.

