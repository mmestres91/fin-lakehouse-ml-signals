variable "bucket_name" {
  description = "Name of the raw S3 bucket"
  type        = string
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
