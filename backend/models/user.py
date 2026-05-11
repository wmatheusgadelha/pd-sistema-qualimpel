from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, Text, Enum, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy import ForeignKey
from backend.core.database import Base
import enum


class RoleEnum(str, enum.Enum):
    admin = "admin"
    gestor = "gestor"
    tecnico = "tecnico"


class StatusProjetoEnum(str, enum.Enum):
    nao_iniciado = "Não iniciado"
    em_andamento = "Em andamento"
    concluido = "Concluído"
    cancelado = "Cancelado"


class TipoContratoEnum(str, enum.Enum):
    full_service = "Full Service"
    servico = "Serviço"


class TipoProjetoEnum(str, enum.Enum):
    novo_produto = "Novo produto"
    extensao_linha = "Extensão de linha"
    reformulacao = "Reformulação"
    rebranding = "Rebranding"


class StatusEtapaEnum(str, enum.Enum):
    nao_iniciado = "Não iniciado"
    em_andamento = "Em andamento"
    concluido = "Concluído"
    nao_aplicavel = "N/A"


class User(Base):
    __tablename__ = "pd_users"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(150), nullable=False)
    email = Column(String(150), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(RoleEnum), default=RoleEnum.tecnico, nullable=False)
    cargo = Column(String(100), nullable=True)
    telefone = Column(String(20), nullable=True)
    matricula = Column(String(30), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Projeto(Base):
    __tablename__ = "projetos"

    id = Column(Integer, primary_key=True, index=True)
    numero = Column(String(20), nullable=True, index=True)
    cliente = Column(String(150), nullable=False)
    marca = Column(String(150), nullable=True)
    produto = Column(String(150), nullable=False)
    tipo_embalagem = Column(String(50), nullable=True)
    gramatura = Column(String(100), nullable=True)
    formulacao = Column(String(100), nullable=True)
    tipo_contrato = Column(Enum(TipoContratoEnum), nullable=False, default=TipoContratoEnum.full_service)
    tipo_projeto = Column(Enum(TipoProjetoEnum), nullable=False, default=TipoProjetoEnum.novo_produto)
    status = Column(Enum(StatusProjetoEnum), nullable=False, default=StatusProjetoEnum.nao_iniciado)
    gestor_id = Column(Integer, nullable=True)
    gestao_externa = Column(String(150), nullable=True)
    previsao_conclusao = Column(Date, nullable=True)
    etapa_atual = Column(String(100), nullable=True)
    progresso = Column(Float, default=0.0)
    proxima_acao = Column(Text, nullable=True)
    observacoes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    etapas = relationship("EtapaProjeto", back_populates="projeto", cascade="all, delete-orphan", order_by="EtapaProjeto.ordem")
    historico = relationship("HistoricoEtapa", back_populates="projeto", cascade="all, delete-orphan")


class EtapaProjeto(Base):
    __tablename__ = "etapas_projeto"

    id = Column(Integer, primary_key=True, index=True)
    projeto_id = Column(Integer, ForeignKey("projetos.id"), nullable=False)
    nome = Column(String(100), nullable=False)
    ordem = Column(Integer, nullable=False)
    status = Column(Enum(StatusEtapaEnum), default=StatusEtapaEnum.nao_iniciado, nullable=False)
    data_conclusao = Column(Date, nullable=True)
    responsavel_id = Column(Integer, nullable=True)
    observacoes = Column(Text, nullable=True)

    projeto = relationship("Projeto", back_populates="etapas")


class HistoricoEtapa(Base):
    __tablename__ = "historico_etapas"

    id = Column(Integer, primary_key=True, index=True)
    projeto_id = Column(Integer, ForeignKey("projetos.id"), nullable=False)
    etapa_nome = Column(String(100), nullable=False)
    status_anterior = Column(String(50), nullable=True)
    status_novo = Column(String(50), nullable=False)
    usuario_id = Column(Integer, nullable=True)
    observacao = Column(Text, nullable=True)
    data = Column(DateTime(timezone=True), server_default=func.now())

    projeto = relationship("Projeto", back_populates="historico")
