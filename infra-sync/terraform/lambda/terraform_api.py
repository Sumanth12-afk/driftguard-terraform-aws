import json
import logging
import os
import time
from typing import Any, Dict, Optional
from urllib import error, request

import boto3
from botocore.exceptions import ClientError

LOGGER = logging.getLogger(__name__)


class TerraformCloudClient:
    """Lightweight Terraform Cloud API client for drift evaluation and remediation."""

    def __init__(
        self,
        org_name: str,
        workspace: str,
        token_secret_arn: str,
        region: str,
        timeout_seconds: int = 3600,
    ) -> None:
        self.org_name = org_name
        self.workspace_name = workspace
        self.timeout_seconds = timeout_seconds
        self._workspace_id: Optional[str] = None
        self._token: Optional[str] = None
        self.api_base_url = os.getenv("TERRAFORM_API_URL", "https://app.terraform.io/api/v2")

        self._secrets_client = boto3.client("secretsmanager", region_name=region)
        self.token_secret_arn = token_secret_arn

    def _resolve_token(self) -> str:
        if self._token:
            return self._token

        try:
            secret_value = self._secrets_client.get_secret_value(SecretId=self.token_secret_arn)
        except ClientError as exc:
            LOGGER.error("Unable to retrieve Terraform API token secret: %s", exc)
            raise

        secret_string = secret_value.get("SecretString")
        if not secret_string:
            raise ValueError("Terraform API token secret is empty or binary; expected SecretString.")

        self._token = secret_string.strip()
        return self._token

    def _request(
        self,
        method: str,
        path: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        token = self._resolve_token()
        url = f"{self.api_base_url.rstrip('/')}/{path.lstrip('/')}"

        data = None
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/vnd.api+json",
        }

        if payload is not None:
            data = json.dumps(payload).encode("utf-8")

        req = request.Request(url, data=data, headers=headers, method=method.upper())
        try:
            with request.urlopen(req, timeout=30) as resp:
                body = resp.read().decode("utf-8")
                return json.loads(body) if body else {}
        except error.HTTPError as http_err:
            detail = http_err.read().decode("utf-8")
            LOGGER.error("Terraform API %s %s failed: %s - %s", method, path, http_err.code, detail)
            raise
        except error.URLError as url_err:
            LOGGER.error("Terraform API unreachable: %s", url_err)
            raise

    def _get_workspace_id(self) -> str:
        if self._workspace_id:
            return self._workspace_id

        path = f"organizations/{self.org_name}/workspaces/{self.workspace_name}"
        response = self._request("GET", path)
        workspace_id = response.get("data", {}).get("id")
        if not workspace_id:
            raise ValueError(f"Unable to resolve workspace ID for {self.workspace_name}")

        self._workspace_id = workspace_id
        return workspace_id

    def create_run(
        self,
        *,
        message: str,
        auto_apply: bool,
    ) -> Dict[str, Any]:
        workspace_id = self._get_workspace_id()

        payload = {
            "data": {
                "type": "runs",
                "attributes": {
                    "is-destroy": False,
                    "message": message[:255],
                    "auto-apply": auto_apply,
                },
                "relationships": {
                    "workspace": {
                        "data": {
                            "type": "workspaces",
                            "id": workspace_id,
                        }
                    }
                },
            }
        }

        LOGGER.info("Creating Terraform plan run for workspace %s", self.workspace_name)
        return self._request("POST", "runs", payload)

    def get_run(self, run_id: str) -> Dict[str, Any]:
        return self._request("GET", f"runs/{run_id}")

    def get_plan(self, plan_id: str) -> Dict[str, Any]:
        return self._request("GET", f"plans/{plan_id}")

    def apply_run(self, run_id: str) -> Dict[str, Any]:
        LOGGER.info("Triggering Terraform apply for run %s", run_id)
        return self._request("POST", f"runs/{run_id}/actions/apply")

    def wait_for_plan(self, run_id: str, poll_interval: int = 10) -> Dict[str, Any]:
        """Poll run until plan is available or terminal state reached."""
        start = time.time()
        terminal_statuses = {"planned", "planned_and_finished", "errored", "canceled", "applied"}

        while time.time() - start < self.timeout_seconds:
            run = self.get_run(run_id)
            status = run.get("data", {}).get("attributes", {}).get("status")
            LOGGER.debug("Run %s status: %s", run_id, status)

            plan_id = (
                run.get("data", {})
                .get("relationships", {})
                .get("plan", {})
                .get("data", {})
                .get("id")
            )

            if plan_id:
                plan = self.get_plan(plan_id)
                has_changes = plan.get("data", {}).get("attributes", {}).get("has-changes")
                attributes = plan.get("data", {}).get("attributes", {})
                resource_changes = attributes.get("resource_changes", {})
                return {
                    "status": status,
                    "plan_id": plan_id,
                    "has_changes": bool(has_changes),
                    "resource_changes": resource_changes,
                }

            if status in terminal_statuses:
                LOGGER.warning("Run %s reached terminal status %s without plan data.", run_id, status)
                return {
                    "status": status,
                    "plan_id": None,
                    "has_changes": False,
                    "resource_changes": {},
                }

            time.sleep(poll_interval)

        raise TimeoutError(f"Timed out waiting for Terraform plan for run {run_id}")

