#!/usr/bin/env bash
#
# scaffold_infra.sh  –  create Terraform skeleton for fin-lakehouse-ml-signals
# usage: bash scaffold_infra.sh

set -euo pipefail

echo "▶️  Scaffolding Terraform directories..."

# 1. core tree
mkdir -p infra/{modules/{network,bucket_raw,iam_ci},dev}

# 2. top-level helper files
cat > infra/.tflint.hcl <<'EOF'
plugin "aws" {
  enabled = true
  version = "0.22.0"
  source  = "github.com/terraform-linters/tflint-ruleset-aws"
}
EOF
touch infra/.tfsecignore

# 3. module placeholders
for mod in network bucket_raw iam_ci; do
  cat > "infra/modules/${mod}/main.tf" <<'EOF'
/* TODO: add real resources */
EOF
  touch "infra/modules/${mod}/variables.tf" "infra/modules/${mod}/outputs.tf"
done

# 4. dev stack stubs
cat > infra/dev/main.tf <<'EOF'
/* Example dev stack – wire modules here */
EOF

cat > infra/dev/versions.tf <<'EOF'
terraform {
  required_version = ">= 1.8.5"
  required_providers {
    aws    = { source = "hashicorp/aws",    version = "~> 5.50" }
    random = { source = "hashicorp/random", version = "~> 3.6"  }
  }
}
EOF

cat > infra/dev/backend.tf <<'EOF'
# Uncomment & fill when ready
# terraform {
#   backend "s3" {
#     bucket = "flmls-tfstate"
#     key    = "dev/terraform.tfstate"
#     region = "us-east-1"
#   }
# }
EOF

echo "✅  Done. Run:\n  terraform -chdir=infra/dev init -backend=false\n  terraform -chdir=infra/dev validate"
