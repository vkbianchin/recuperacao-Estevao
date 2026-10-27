from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

class Usuario(Base):
    __tablename__ = "usuarios"
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, index=True, nullable=False)
    senha_hash = Column(String(255), nullable=False)
    papel = Column(String(20), nullable=False, default="comum")

class Equipamento(Base):
    __tablename__ = "equipamentos"
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(120), nullable=False)
    descricao = Column(Text, nullable=True)
    patrimonio = Column(String(50), unique=True, nullable=False)
    disponivel = Column(Boolean, nullable=False, default=True)

class Emprestimo(Base):
    __tablename__ = "emprestimos"
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    equipamento_id = Column(Integer, ForeignKey("equipamentos.id"), nullable=False)
    status = Column(String(20), nullable=False, default="solicitado")
    solicitado_em = Column(DateTime(timezone=True), server_default=func.now())
    aprovado_por = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    aprovado_em = Column(DateTime(timezone=True), nullable=True)
    devolvido_por = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    devolvido_em = Column(DateTime(timezone=True), nullable=True)
    usuario = relationship("Usuario", foreign_keys=[usuario_id])
    equipamento = relationship("Equipamento")
