provider "aws" {
  region = var.aws_region
}

module "raw" {
  source            = "../modules/s3_bucket"
  bucket_name       = var.bucket_name_raw
  env               = "dev"
  enable_versioning = true
  log_bucket_name   = module.logs.bucket_name
}

module "curated" {
  source            = "../modules/s3_bucket"
  bucket_name       = var.bucket_name_curated
  env               = "dev"
  enable_versioning = true
  log_bucket_name   = module.logs.bucket_name
}

module "features" {
  source            = "../modules/s3_bucket"
  bucket_name       = var.bucket_name_features
  env               = "dev"
  enable_versioning = true
  log_bucket_name   = module.logs.bucket_name
}

module "logs" {
  source            = "../modules/s3_bucket"
  bucket_name       = var.bucket_name_logs
  env               = var.env
  enable_versioning = true
  log_bucket_name   = ""
}