##############################
#  CloudFront for GE docs   ##
##############################

data "aws_caller_identity" "current" {}
data "aws_kms_key" "s3_cmk" { key_id = data.aws_kms_alias.s3_cmk.target_key_id }
data "aws_kms_alias" "s3_cmk" { name = "alias/s3-cmk" }

# ① Private access identity
resource "aws_cloudfront_origin_access_identity" "ge_docs" {
  comment = "OAI for GE Data Docs"
}

# ② Attach an S3 bucket policy that lets ONLY the OAI read objects

data "aws_iam_policy_document" "ge_docs_bucket" {
  statement {
    sid    = "AllowCloudFrontRead"
    effect = "Allow"

    principals {
      type        = "AWS"
      identifiers = [aws_cloudfront_origin_access_identity.ge_docs.iam_arn]
    }

    actions   = ["s3:GetObject"]
    resources = ["${module.logs.bucket_arn}/*"]
  }
}

resource "aws_s3_bucket_policy" "ge_docs" {
  bucket = module.logs.bucket_id
  policy = data.aws_iam_policy_document.ge_docs_bucket.json
}

# ③ Update your CMK so S3 can decrypt objects

data "aws_iam_policy_document" "kms_cf_docs" {

  # ➊ Default statement that AWS creates on every CMK
  statement {
    sid    = "EnableIAMUserPermissions"
    effect = "Allow"

    principals {
      type        = "AWS"
      identifiers = ["arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"]
    }

    actions   = ["kms:*"]
    resources = ["*"]
  }

  # ➋ Extra rights for CloudFront OAI
  statement {
    sid    = "AllowCloudFrontDecrypt"
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["cloudfront.amazonaws.com"]
    }

    actions = [
      "kms:Decrypt",
      "kms:Encrypt",
      "kms:ReEncrypt*",
      "kms:GenerateDataKey*"
    ]

    condition {
      test     = "StringEquals"
      variable = "kms:ViaService"
      values   = ["s3.${var.aws_region}.amazonaws.com"]
    }

    resources = ["*"]
  }
}

# ── apply the merged document ─────────────────────────────────
resource "aws_kms_key_policy" "s3_cmk_patch" {
  key_id = data.aws_kms_key.s3_cmk.id
  policy = data.aws_iam_policy_document.kms_cf_docs.json
}

# ④ CloudFront distribution
resource "aws_cloudfront_distribution" "ge_docs" {
  enabled             = true
  default_root_object = "index.html"

  origin {
    origin_id   = "s3-ge-docs"
    domain_name = module.logs.bucket_regional_domain_name # ← this one

    s3_origin_config {
      origin_access_identity = aws_cloudfront_origin_access_identity.ge_docs.cloudfront_access_identity_path
    }
  }

  default_cache_behavior {
    target_origin_id       = "s3-ge-docs"
    viewer_protocol_policy = "redirect-to-https"

    allowed_methods = ["GET", "HEAD"]
    cached_methods  = ["GET", "HEAD"]

    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }
  }

  price_class  = "PriceClass_100" # lowest cost (you can change)
  http_version = "http2"

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true # keep default *.cloudfront.net
  }

  tags = {
    Environment = var.env
    Terraform   = "true"
  }
}

output "ge_docs_url" {
  value = "https://${aws_cloudfront_distribution.ge_docs.domain_name}"
}
