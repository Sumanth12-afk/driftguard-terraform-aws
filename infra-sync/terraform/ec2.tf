data "aws_vpc" "default" {
  count   = var.create_test_ec2 ? 1 : 0
  default = true
}

data "aws_subnets" "default" {
  count = var.create_test_ec2 ? 1 : 0

  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default[0].id]
  }
}

data "aws_ami" "al2023" {
  count = var.create_test_ec2 ? 1 : 0

  owners      = ["amazon"]
  most_recent = true

  filter {
    name   = "name"
    values = ["al2023-ami-*-x86_64"]
  }

  filter {
    name   = "architecture"
    values = ["x86_64"]
  }
}

locals {
  ec2_subnet_id = var.create_test_ec2 ? (
    var.ec2_subnet_id != null ?
    var.ec2_subnet_id :
    try(data.aws_subnets.default[0].ids[0], null)
  ) : null
}

resource "aws_instance" "drift_guard_test" {
  count         = var.create_test_ec2 ? 1 : 0
  ami           = data.aws_ami.al2023[0].id
  instance_type = var.ec2_instance_type
  subnet_id     = local.ec2_subnet_id

  associate_public_ip_address = true
  key_name                    = var.ec2_key_name

  tags = merge(
    local.common_tags,
    {
      Name = "${local.project_name}-drift-test"
    },
    var.ec2_additional_tags
  )

  lifecycle {
    ignore_changes = [tags]
  }
}

output "test_instance_id" {
  description = "ID of the optional EC2 test instance."
  value       = try(aws_instance.drift_guard_test[0].id, null)
}

