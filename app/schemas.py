"""Modelos Pydantic com as regras de validação."""
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class AlunoBase(BaseModel):
    nome: str = Field(..., examples=["João Silva"])
    email: EmailStr = Field(..., examples=["joao@email.com"])
    idade: int = Field(..., ge=16, examples=[22], description="Idade mínima: 16 anos")
    curso: str = Field(..., examples=["Ciência da Computação"])

    @field_validator("nome", "curso")
    @classmethod
    def nao_vazio(cls, valor: str) -> str:
        valor = valor.strip()
        if not valor:
            raise ValueError("não pode ser vazio")
        return valor

    @field_validator("email")
    @classmethod
    def normalizar_email(cls, valor: str) -> str:
        return valor.lower()


class AlunoCreate(AlunoBase):
    pass


class AlunoUpdate(AlunoBase):
    pass


class AlunoResponse(AlunoBase):
    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(..., examples=["68c123..."])


class Mensagem(BaseModel):
    mensagem: str
    aluno: AlunoResponse | None = None
