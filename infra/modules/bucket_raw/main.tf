terraform {
  required_version = ">= 1.8.0"
}

resource "aws_s3_bucket" "raw" {
  bucket = var.bucket_name

  force_destroy = true

  tags = {
    Environment = var.env
    Terraform   = "true"
  }
}

resource "aws_s3_bucket_versioning" "this" {
  bucket = aws_s3_bucket.raw.id

  versioning_configuration {
    status = var.enable_versioning ? "Enabled" : "Suspended"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "this" {
  bucket = aws_s3_bucket.raw.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.s3_cmk.arn
    }
  }
}

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "raw" {
  bucket                  = aws_s3_bucket.raw.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket" "log_target" {
  bucket        = "finlakehouse-logs-mmestres91"
  force_destroy = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "log_target" {
  bucket = aws_s3_bucket.log_target.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.s3_cmk.arn
    }
  }
}

resource "aws_s3_bucket_public_access_block" "log_target" {
  bucket                  = aws_s3_bucket.log_target.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "log_target" {
  bucket = aws_s3_bucket.log_target.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_logging" "log_target" {
  bucket = aws_s3_bucket.log_target.id

  target_bucket = aws_s3_bucket.log_target.id
  target_prefix = "log/"
}

resource "aws_s3_bucket_logging" "raw" {
  bucket = aws_s3_bucket.raw.id

  target_bucket = aws_s3_bucket.log_target.id
  target_prefix = "log/"
}

resource "aws_kms_key" "s3_cmk" {
  description             = "CMK for S3 bucket encryption"
  deletion_window_in_days = 7
  enable_key_rotation     = true
}

resource "aws_kms_alias" "s3_cmk_alias" {
  name          = "alias/s3-cmk"
  target_key_id = aws_kms_key.s3_cmk.key_id
}
