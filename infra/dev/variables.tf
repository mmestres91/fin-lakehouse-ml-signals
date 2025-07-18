variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "bucket_name_raw" {
  description = "finlakehouse-raw-mmestres91"
  type        = string
}

variable "bucket_name_curated" {
  description = "finlakehouse-curated-mmestres91"
  type        = string
}

variable "bucket_name_features" {
  description = "finlakehouse-features-mmestres91"
  type        = string
}

variable "env" {
  description = "Environment name (e.g., dev, prod)"
  type        = string
}

variable "bucket_name_logs" {
  description = "S3 bucket for all other buckets to ship their server‑access and data‑docs logs into"
  type        = string
  default     = "finlakehouse-logs-mmestres91"
}