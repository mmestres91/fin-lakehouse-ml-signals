variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "bucket_name_raw" {
  type    = string
  default = "finlakehouse-raw-mmestres91"
}

variable "bucket_name_curated" {
  type    = string
  default = "finlakehouse-curated-mmestres91"
}