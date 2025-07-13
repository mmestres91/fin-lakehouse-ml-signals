terraform {
  required_version = ">= 1.8.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# trivy:ignore:AVD-AWS-0089
resource "aws_s3_bucket" "curated" {
  bucket        = var.bucket_name
  force_destroy = true

  logging {
    target_bucket = "finlakehouse-logs-mmestres91"
    target_prefix = "curated/"
  }

  tags = {
    Environment = var.env
    Terraform   = "true"
  }
}

resource "aws_s3_bucket_versioning" "this" {
  bucket = aws_s3_bucket.curated.id

  versioning_configuration {
    status = var.enable_versioning ? "Enabled" : "Suspended"
  }
}

resource "aws_s3_bucket_public_access_block" "curated" {
  bucket                  = aws_s3_bucket.curated.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

data "aws_kms_alias" "s3_cmk" {
  name = "alias/s3-cmk" # same alias the raw module made
}

resource "aws_s3_bucket_server_side_encryption_configuration" "this" {
  bucket = aws_s3_bucket.curated.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = data.aws_kms_alias.s3_cmk.arn
    }
  }
}
