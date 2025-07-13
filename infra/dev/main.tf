provider "aws" {
  region = var.aws_region
}

module "bucket_raw" {
  source            = "../modules/bucket_raw"
  bucket_name       = var.bucket_name_raw
  env               = "dev"
  enable_versioning = true
}

module "bucket_curated" {
  source            = "../modules/bucket_curated"
  bucket_name       = var.bucket_name_curated
  log_bucket_name   = "finlakehouse-logs-mmestres91"
  env               = "dev"
  enable_versioning = true
}