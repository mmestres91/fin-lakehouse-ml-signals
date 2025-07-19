terraform {
  required_version = ">= 1.8.0"
}

output "bucket_name" {
  value = aws_s3_bucket.this.bucket
}

output "bucket_id" {
  value = aws_s3_bucket.this.id
}

output "bucket_arn" {
  value = aws_s3_bucket.this.arn
}

output "bucket_regional_domain_name" {
  description = "Regional DNS name of the bucket (e.g. finlakehouse‑logs‑...s3.us‑east‑1.amazonaws.com)"
  value       = aws_s3_bucket.this.bucket_regional_domain_name
}