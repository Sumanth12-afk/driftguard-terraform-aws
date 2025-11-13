import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)

AWS_REGION = os.environ.get("AWS_REGION", "ap-south-1")
TERRAFORM_ORG = os.environ.get("TERRAFORM_ORG_NAME")
TERRAFORM_WORKSPACE = os.environ.get("TERRAFORM_WORKSPACE")
TERRAFORM_TOKEN_SECRET_ARN = os.environ.get("TERRAFORM_API_TOKEN_SECRET_ARN")
SLACK_WEBHOOK_SECRET_ARN = os.environ.get("SLACK_WEBHOOK_SECRET_ARN")
DRIFT_HISTORY_TABLE = os.environ.get("DRIFT_HISTORY_TABLE_NAME")
AUTO_REMEDIATE = os.environ.get("AUTO_REMEDIATE", "false").lower() == "true"

if not all(
    [
        TERRAFORM_ORG,
        TERRAFORM_WORKSPACE,
        TERRAFORM_TOKEN_SECRET_ARN,
        SLACK_WEBHOOK_SECRET_ARN,
        DRIFT_HISTORY_TABLE,
    ]
):
    LOGGER.error("Missing required environment configuration. Lambda will fail fast.")

from dynamodb_logger import DriftHistoryLogger  # noqa: E402
from slack_notifier import SlackNotifier, build_slack_payload  # noqa: E402
from terraform_api import TerraformCloudClient  # noqa: E402


def lambda_handler(event: Dict[str, Any], _context: Any) -> Dict[str, Any]:
    LOGGER.info("Received event: %s", json.dumps(event))

    resource_summary = parse_resource_details(event)
    detected_at = datetime.now(timezone.utc)

    tf_client = TerraformCloudClient(
        TERRAFORM_ORG,
        TERRAFORM_WORKSPACE,
        TERRAFORM_TOKEN_SECRET_ARN,
        AWS_REGION,
    )

    notifier = SlackNotifier(SLACK_WEBHOOK_SECRET_ARN, AWS_REGION)
    history_logger = DriftHistoryLogger(DRIFT_HISTORY_TABLE, AWS_REGION)

    message = (
        f"InfraSync DriftGuard automated check triggered by {resource_summary['resource_type']} "
        f"{resource_summary['resource_id']} at {detected_at.isoformat()}."
    )

    run = tf_client.create_run(message=message, auto_apply=AUTO_REMEDIATE)
    run_id = run.get("data", {}).get("id")
    if not run_id:
        raise RuntimeError("Terraform run creation failed; no run ID returned.")

    plan_result = tf_client.wait_for_plan(run_id)
    has_drift = plan_result.get("has_changes", False)
    change_summary = summarize_plan(plan_result.get("resource_changes", {}))

    status = "Pending Remediation" if has_drift else "No Drift Detected"

    slack_payload = build_slack_payload(
        title="✅ InfraSync DriftGuard - No Drift" if not has_drift else "⚠️ InfraSync DriftGuard - Drift Detected",
        resource_id=resource_summary["resource_id"],
        resource_type=resource_summary["resource_type"],
        change_type=change_summary or resource_summary["change_type"],
        detected_at=detected_at.isoformat(),
        status=status,
        detail_url=build_run_url(run_id),
    )

    if has_drift:
        LOGGER.warning("Drift detected for %s", resource_summary["resource_id"])
        notifier.send_alert(slack_payload)

        history_logger.put_record(
            resource_summary["resource_id"],
            resource_summary["resource_type"],
            resource_summary["change_type"],
            detected_at,
            "Pending" if AUTO_REMEDIATE else "Detected",
            {
                "plan_status": plan_result.get("status"),
                "resource_changes": plan_result.get("resource_changes"),
                "event_detail": resource_summary,
            },
        )

        if AUTO_REMEDIATE:
            remediation_result = tf_client.apply_run(run_id)
            LOGGER.info("Triggered Terraform apply: %s", remediation_result)
    else:
        LOGGER.info("No drift detected. Sending informational alert.")
        notifier.send_alert(slack_payload)

        history_logger.put_record(
            resource_summary["resource_id"],
            resource_summary["resource_type"],
            resource_summary["change_type"],
            detected_at,
            "NoDrift",
            {
                "plan_status": plan_result.get("status"),
                "resource_changes": plan_result.get("resource_changes"),
                "event_detail": resource_summary,
            },
        )

    return {
        "resource": resource_summary,
        "has_drift": has_drift,
        "status": status,
        "run_id": run_id,
    }


def parse_resource_details(event: Dict[str, Any]) -> Dict[str, Any]:
    detail = event.get("detail", {})
    resource_id = "unknown"
    resource_type = detail.get("eventSource", "unknown")
    change_type = detail.get("eventName", "unknown")

    resources = detail.get("resources") or event.get("resources")
    if isinstance(resources, list) and resources:
        resource_id = resources[0].get("ARN") or resources[0].get("resourceName", resource_id)

    request_params = detail.get("requestParameters", {})
    response_elements = detail.get("responseElements", {})

    if resource_id == "unknown":
        candidate_keys = ["bucketName", "userName", "roleName", "instanceId", "groupName"]
        for key in candidate_keys:
            candidate = request_params.get(key) or response_elements.get(key)
            if candidate:
                resource_id = candidate
                break

    return {
        "resource_id": str(resource_id),
        "resource_type": str(resource_type),
        "change_type": str(change_type),
        "request_parameters": request_params,
        "response_elements": response_elements,
    }


def summarize_plan(resource_changes: Any) -> str:
    if not resource_changes:
        return ""

    additions = 0
    updates = 0
    deletions = 0

    if isinstance(resource_changes, dict):
        additions = resource_changes.get("add", 0)
        updates = resource_changes.get("change", 0)
        deletions = resource_changes.get("destroy", 0)
    elif isinstance(resource_changes, list):
        for change in resource_changes:
            actions = change.get("change", {}).get("actions", []) if isinstance(change, dict) else []
            actions_set = set(actions)
            if "create" in actions_set:
                additions += 1
            if "update" in actions_set:
                updates += 1
            if "delete" in actions_set or "destroy" in actions_set:
                deletions += 1

    parts = []
    if additions:
        parts.append(f"{additions} to add")
    if updates:
        parts.append(f"{updates} to change")
    if deletions:
        parts.append(f"{deletions} to destroy")

    return ", ".join(parts)


def build_run_url(run_id: Optional[str]) -> Optional[str]:
    if not run_id:
        return None
    return f"https://app.terraform.io/app/{TERRAFORM_ORG}/workspaces/{TERRAFORM_WORKSPACE}/runs/{run_id}"

