DriftGuard – Terraform Drift Detection System

## What the Solution Does

DriftGuard detects configuration drift between your AWS environment and Terraform-managed infrastructure. It alerts or optionally auto-remediates deviations.

## Why It Exists

Manual AWS console changes cause environments to drift away from Terraform state, resulting in:

- Inconsistent deployments
- Failed pipelines
- Security gaps
- Operational risk

This system enforces IaC consistency.

## Use Cases

- Teams using Terraform Cloud
- Regulated industries needing infra compliance
- Large multi-team AWS environments
- Environments prone to console/manual changes

## High-Level Architecture

- EventBridge periodic triggers
- Lambda compares live AWS state vs Terraform state
- Drift report stored in DynamoDB
- Alerts sent to Slack
- Optional automated remediation

## Features

- Real-time drift detection
- Dashboard-ready reporting
- Slack notifications
- Deep service-level comparison
- Optional safe remediation

## Benefits

- Stronger infrastructure governance
- Reduced outages from misconfigurations
- Compliance with IaC best practices
- Predictable deployments

## Business Problem It Solves

Infrastructure drift is a silent threat that causes unpredictable behavior. DriftGuard continuously restores alignment between desired and actual state.

## How It Works (Non-Code Workflow)

DriftDetector Lambda runs at scheduled intervals. System fetches Terraform state from Terraform Cloud. Live AWS resources are compared against expected configuration. Drift is logged and reported. Optional remediation restores correct settings.

## Additional Explanation

DriftGuard can be extended to integrate with dashboards, SIEM tools, or additional resource types.
