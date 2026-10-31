# Exemplo propositalmente com problemas para testar a revisão:
# usuário IAM com access key e política que libera tudo em todos os recursos.

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

resource "aws_iam_user" "deploy" {
  name = "deploy"
}

resource "aws_iam_access_key" "deploy" {
  user = aws_iam_user.deploy.name
}

resource "aws_iam_user_policy" "deploy" {
  name = "deploy"
  user = aws_iam_user.deploy.name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = "*"
        Resource = "*"
      }
    ]
  })
}

output "deploy_secret_access_key" {
  value     = aws_iam_access_key.deploy.secret
  sensitive = true
}
