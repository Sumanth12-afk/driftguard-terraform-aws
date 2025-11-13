import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import boto3

LOGGER = logging.getLogger(__name__)


class DriftHistoryLogger:
    """Persists drift events to DynamoDB with optional TTL."""

    def __init__(
        self,
        table_name: str,
        region: str,
        ttl_days: Optional[int] = 90,
    ) -> None:
        self.table_name = table_name
        self.region = region
        self.ttl_days = ttl_days
        self._client = boto3.client("dynamodb", region_name=region)

    def put_record(
        self,
        resource_id: str,
        resource_type: str,
        change_type: str,
        detected_at: datetime,
        status: str,
        details: Dict[str, Any],
    ) -> None:
        ttl_epoch = None
        if self.ttl_days and self.ttl_days > 0:
            ttl_epoch = int((detected_at + timedelta(days=self.ttl_days)).timestamp())

        item = {
            "ResourceID": {"S": resource_id},
            "DetectedAt": {"S": detected_at.isoformat()},
            "ResourceType": {"S": resource_type},
            "ChangeType": {"S": change_type},
            "Status": {"S": status},
            "Details": {"S": json_dump(details)},
        }

        if ttl_epoch:
            item["TimeToExpire"] = {"N": str(ttl_epoch)}

        LOGGER.debug("Writing drift record for %s to DynamoDB", resource_id)
        self._client.put_item(TableName=self.table_name, Item=item)


def json_dump(value: Dict[str, Any]) -> str:
    """Serialize dict to stable JSON string."""
    import json

    return json.dumps(value, sort_keys=True, default=str)

