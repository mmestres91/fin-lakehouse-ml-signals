variable "bucket_name" {
  description = "The name of the S3 bucket to create"
  type        = string
  default     = "dummy-curated" # <─ placeholder for scanners only
}

variable "env" {
  description = "Environment name (e.g., dev, prod)"
  type        = string
}

variable "enable_versioning" {
  description = "Enable versioning?"
  type        = bool
  default     = true
}

variable "log_bucket_name" {
  type        = string
  description = "Optional target bucket for server‑access logs"
  default     = "finlakehouse-logs-mmestres91"
}