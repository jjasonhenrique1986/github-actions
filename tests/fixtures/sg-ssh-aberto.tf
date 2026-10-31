# Fixture propositalmente inseguro para o teste com AWS da action iac-ai-review.
# Não aplique este arquivo numa conta de verdade.

resource "aws_security_group" "web" {
  name        = "web"
  description = "Acesso ao servidor web"

  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
