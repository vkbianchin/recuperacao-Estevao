from pydantic import BaseModel, EmailStr, ConfigDict, Field
from typing import Optional

class LoginIn(BaseModel):
    email: EmailStr
    senha: str

class UsuarioCreate(BaseModel):
    nome: str = Field(min_length=2, max_length=100)
    email: EmailStr
    senha: str = Field(min_length=8)
    papel: str = "comum"

class UsuarioOut(BaseModel):
    id: int
    nome: str
    email: EmailStr
    papel: str
    model_config = ConfigDict(from_attributes=True)

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"

class EquipamentoCreate(BaseModel):
    nome: str = Field(min_length=2, max_length=120)
    descricao: Optional[str] = None
    patrimonio: str = Field(min_length=1, max_length=50)

class EquipamentoOut(BaseModel):
    id: int
    nome: str
    descricao: Optional[str]
    patrimonio: str
    disponivel: bool
    model_config = ConfigDict(from_attributes=True)

class EmprestimoCreate(BaseModel):
    equipamento_id: int

class EmprestimoOut(BaseModel):
    id: int
    usuario_id: int
    equipamento_id: int
    status: str
    solicitado_em: Optional[str] = None
    aprovado_por: Optional[int] = None
    devolvido_por: Optional[int] = None
    model_config = ConfigDict(from_attributes=True)
