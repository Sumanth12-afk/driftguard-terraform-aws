resource "aws_dynamodb_table" "drift_history" {
  name         = "${local.project_name}-drift-history"
  billing_mode = "PAY_PER_REQUEST"

  hash_key  = "ResourceID"
  range_key = "DetectedAt"

  attribute {
    name = "ResourceID"
    type = "S"
  }

  attribute {
    name = "DetectedAt"
    type = "S"
  }

  ttl {
    attribute_name = "TimeToExpire"
    enabled        = true
  }

  point_in_time_recovery {
    enabled = var.dynamodb_point_in_time_recovery
  }

  server_side_encryption {
    enabled = true
  }

  tags = merge(
    local.common_tags,
    {
      DataClassification = "Confidential"
    }
  )
}

