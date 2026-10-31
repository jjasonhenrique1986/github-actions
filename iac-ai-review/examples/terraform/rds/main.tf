# Exemplo propositalmente com problemas para testar a revisão:
# banco acessível pela internet, sem criptografia, senha no código e sem backup.

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

resource "aws_db_instance" "app" {
  identifier          = "app-db"
  engine              = "postgres"
  engine_version      = "17"
  instance_class      = "db.t4g.micro"
  allocated_storage   = 20
  username            = "app"
  password            = "SenhaFixa123!"
  publicly_accessible = true
  storage_encrypted   = false

  backup_retention_period = 0
  skip_final_snapshot     = true
  deletion_protection     = false
}
