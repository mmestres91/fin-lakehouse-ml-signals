terraform {
  required_version = ">= 1.8.0"
}

output "bucket_name" {
  value = aws_s3_bucket.raw.bucket
}

output "s3_kms_key_id" {
  value = aws_kms_key.s3_cmk.key_id
}