import json
import logging
import os
from typing import Any, Dict, Optional
from urllib import request, error

import boto3
from botocore.exceptions import ClientError

LOGGER = logging.getLogger(__name__)


class SlackNotifier:
    """Posts drift notifications to Slack via webhook stored in Secrets Manager."""

    def __init__(self, webhook_secret_arn: str, region: str) -> None:
        self.webhook_secret_arn = webhook_secret_arn
        self.region = region
        self._webhook_url: Optional[str] = None
        self._secrets_client = boto3.client("secretsmanager", region_name=region)

    def _resolve_webhook(self) -> str:
        if self._webhook_url:
            return self._webhook_url

        try:
            response = self._secrets_client.get_secret_value(SecretId=self.webhook_secret_arn)
        except ClientError as exc:
            LOGGER.error("Unable to fetch Slack webhook secret: %s", exc)
            raise

        secret_string = response.get("SecretString")
        if not secret_string:
            raise ValueError("Slack webhook secret must contain a SecretString.")

        self._webhook_url = secret_string.strip()
        return self._webhook_url

    def send_alert(self, payload: Dict[str, Any]) -> None:
        webhook = self._resolve_webhook()
        message = json.dumps(payload).encode("utf-8")
        req = request.Request(
            webhook,
            data=message,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with request.urlopen(req, timeout=10) as resp:
                if resp.status >= 300:
                    detail = resp.read().decode("utf-8")
                    raise RuntimeError(f"Slack webhook returned {resp.status}: {detail}")
        except error.HTTPError as http_err:
            detail = http_err.read().decode("utf-8")
            LOGGER.error("Slack webhook failed: %s - %s", http_err.code, detail)
            raise
        except error.URLError as url_err:
            LOGGER.error("Slack webhook unreachable: %s", url_err)
            raise


def build_slack_payload(
    *,
    title: str,
    resource_id: str,
    resource_type: str,
    change_type: str,
    detected_at: str,
    status: str,
    detail_url: Optional[str],
) -> Dict[str, Any]:
    blocks: list[Dict[str, Any]] = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*{title}*",
            },
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Resource ID:*\n{resource_id}"},
                {"type": "mrkdwn", "text": f"*Resource Type:*\n{resource_type}"},
                {"type": "mrkdwn", "text": f"*Change Type:*\n{change_type}"},
                {"type": "mrkdwn", "text": f"*Status:*\n{status}"},
                {"type": "mrkdwn", "text": f"*Detected At:*\n{detected_at}"},
            ],
        },
    ]

    if detail_url:
        blocks.append(
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "View in Terraform Cloud"},
                        "url": detail_url,
                    }
                ],
            }
        )

    return {"blocks": blocks}

