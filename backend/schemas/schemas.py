from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import date, datetime
from enum import Enum


# ─── Enums ────────────────────────────────────────────────────────────────────

class RoleEnum(str, Enum):
    admin = "admin"
    gestor = "gestor"
    tecnico = "tecnico"


class StatusProjetoEnum(str, Enum):
    nao_iniciado = "Não iniciado"
    em_andamento = "Em andamento"
    concluido = "Concluído"
    cancelado = "Cancelado"


class TipoContratoEnum(str, Enum):
    full_service = "Full Service"
    servico = "Serviço"


class TipoProjetoEnum(str, Enum):
    novo_produto = "Novo produto"
    extensao_linha = "Extensão de linha"
    reformulacao = "Reformulação"
    rebranding = "Rebranding"


class StatusEtapaEnum(str, Enum):
    nao_iniciado = "Não iniciado"
    em_andamento = "Em andamento"
    concluido = "Concluído"
    nao_aplicavel = "N/A"


# ─── User ─────────────────────────────────────────────────────────────────────

class UserBase(BaseModel):
    nome: str
    email: EmailStr
    role: RoleEnum = RoleEnum.tecnico
    cargo: Optional[str] = None
    telefone: Optional[str] = None
    matricula: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    nome: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[RoleEnum] = None
    cargo: Optional[str] = None
    telefone: Optional[str] = None
    matricula: Optional[str] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ChangePassword(BaseModel):
    senha_atual: str
    nova_senha: str


# ─── Etapa ────────────────────────────────────────────────────────────────────

class EtapaUpdate(BaseModel):
    status: StatusEtapaEnum
    data_conclusao: Optional[date] = None
    responsavel_id: Optional[int] = None
    observacoes: Optional[str] = None


class EtapaResponse(BaseModel):
    id: int
    nome: str
    ordem: int
    status: StatusEtapaEnum
    data_conclusao: Optional[date] = None
    responsavel_id: Optional[int] = None
    observacoes: Optional[str] = None

    class Config:
        from_attributes = True


# ─── Projeto ──────────────────────────────────────────────────────────────────

class ProjetoCreate(BaseModel):
    numero: Optional[str] = None
    cliente: str
    marca: Optional[str] = None
    produto: str
    tipo_embalagem: Optional[str] = None
    gramatura: Optional[str] = None
    formulacao: Optional[str] = None
    tipo_contrato: TipoContratoEnum = TipoContratoEnum.full_service
    tipo_projeto: TipoProjetoEnum = TipoProjetoEnum.novo_produto
    status: StatusProjetoEnum = StatusProjetoEnum.nao_iniciado
    gestor_id: Optional[int] = None
    gestao_externa: Optional[str] = None
    previsao_conclusao: Optional[date] = None
    proxima_acao: Optional[str] = None
    observacoes: Optional[str] = None


class ProjetoUpdate(BaseModel):
    numero: Optional[str] = None
    cliente: Optional[str] = None
    marca: Optional[str] = None
    produto: Optional[str] = None
    tipo_embalagem: Optional[str] = None
    gramatura: Optional[str] = None
    formulacao: Optional[str] = None
    tipo_contrato: Optional[TipoContratoEnum] = None
    tipo_projeto: Optional[TipoProjetoEnum] = None
    status: Optional[StatusProjetoEnum] = None
    gestor_id: Optional[int] = None
    gestao_externa: Optional[str] = None
    previsao_conclusao: Optional[date] = None
    proxima_acao: Optional[str] = None
    observacoes: Optional[str] = None


class ProjetoResponse(BaseModel):
    id: int
    numero: Optional[str]
    cliente: str
    marca: Optional[str]
    produto: str
    tipo_embalagem: Optional[str]
    gramatura: Optional[str]
    formulacao: Optional[str]
    tipo_contrato: TipoContratoEnum
    tipo_projeto: TipoProjetoEnum
    status: StatusProjetoEnum
    gestor_id: Optional[int]
    gestao_externa: Optional[str]
    previsao_conclusao: Optional[date]
    etapa_atual: Optional[str]
    progresso: float
    proxima_acao: Optional[str]
    observacoes: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    etapas: List[EtapaResponse] = []

    class Config:
        from_attributes = True


# ─── Histórico ────────────────────────────────────────────────────────────────

class HistoricoResponse(BaseModel):
    id: int
    etapa_nome: str
    status_anterior: Optional[str]
    status_novo: str
    usuario_id: Optional[int]
    observacao: Optional[str]
    data: datetime

    class Config:
        from_attributes = True


# ─── Dashboard ────────────────────────────────────────────────────────────────

class DashboardStats(BaseModel):
    total_projetos: int
    em_andamento: int
    concluidos: int
    nao_iniciados: int
    cancelados: int
    por_cliente: dict
    por_tipo_contrato: dict
    por_tipo_projeto: dict
    progresso_medio: float
