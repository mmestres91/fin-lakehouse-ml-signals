provider "aws" {
  region = var.aws_region
}

module "bucket_raw" {
  source            = "../modules/bucket_raw"
  bucket_name       = var.bucket_name
  env               = "dev"
  enable_versioning = true
}
