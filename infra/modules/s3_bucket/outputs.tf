terraform {
  required_version = ">= 1.8.0"
}

output "bucket_name" {
  value = aws_s3_bucket.this.bucket
}
