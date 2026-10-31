# Exemplo propositalmente com problemas para testar a revisão:
# endpoint da API do cluster aberto para a internet, sem logs do control plane
# e sem criptografia dos Secrets com KMS.

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

variable "cluster_role_arn" {
  type = string
}

variable "subnet_ids" {
  type = list(string)
}

resource "aws_eks_cluster" "app" {
  name     = "app"
  role_arn = var.cluster_role_arn

  vpc_config {
    subnet_ids              = var.subnet_ids
    endpoint_public_access  = true
    endpoint_private_access = false
    public_access_cidrs     = ["0.0.0.0/0"]
  }
}
