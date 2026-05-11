from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
from datetime import date
import os

from backend.core.database import engine, SessionLocal, Base
from backend.core.security import get_password_hash
from backend.models.user import (
    User, Projeto, EtapaProjeto, HistoricoEtapa,
    RoleEnum, StatusProjetoEnum, TipoContratoEnum, TipoProjetoEnum, StatusEtapaEnum
)
from backend.routers import auth, users, projetos, dashboard

ETAPAS_PADRAO = [
    "Sinal", "Negociação", "Formalização", "Amostra",
    "Embalagem EAN / DUN", "Embalagem - Ficha Técnica",
    "Embalagem - Planta Técnica", "Embalagem - Dizeres de Rotulagem",
    "Embalagem - Rotas Criativas", "Embalagem - Planificação",
    "Embalagem - Caixa de Embarque", "Clicheria",
    "Embalagem - Impressão", "Produção",
]

def criar_etapas(db, projeto_id, etapas_concluidas=None, etapas_andamento=None):
    etapas_concluidas = etapas_concluidas or []
    etapas_andamento = etapas_andamento or []
    for i, nome in enumerate(ETAPAS_PADRAO):
        if nome in etapas_concluidas:
            status = StatusEtapaEnum.concluido
        elif nome in etapas_andamento:
            status = StatusEtapaEnum.em_andamento
        else:
            status = StatusEtapaEnum.nao_iniciado
        db.add(EtapaProjeto(
            projeto_id=projeto_id, nome=nome, ordem=i+1, status=status,
            data_conclusao=date(2025, 6, 1) if status == StatusEtapaEnum.concluido else None,
        ))

def calcular_progresso(concluidas):
    return round(len(concluidas) / len(ETAPAS_PADRAO), 2)

def criar_usuario(db, email, nome, senha, role, cargo):
    u = User(nome=nome, email=email, hashed_password=get_password_hash(senha),
             role=role, cargo=cargo, is_active=True)
    db.add(u)
    db.flush()
    db.refresh(u)
    return u

def add_projeto(db, **kwargs):
    etapas_c = kwargs.pop('etapas_c', [])
    etapas_a = kwargs.pop('etapas_a', [])
    p = Projeto(**kwargs)
    db.add(p); db.flush()
    criar_etapas(db, p.id, etapas_c, etapas_a)
    return p

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        reset_seed = os.getenv("RESET_SEED", "false").lower() == "true"
        if reset_seed:
            db.query(HistoricoEtapa).delete()
            db.query(EtapaProjeto).delete()
            db.query(Projeto).delete()
            db.query(User).delete()
            db.commit()
            print("Seed resetado!")

        if db.query(Projeto).count() == 0:
            criar_usuario(db, "admin@pd.com", "Administrador", "admin123", RoleEnum.admin, "Administrador do Sistema")
            criar_usuario(db, "willian@qualimpel.com", "Willian Gadelha", "qualimpel123", RoleEnum.gestor, "Gestor de P&D")
            criar_usuario(db, "marcos@qualimpel.com", "Marcos Wichoski", "qualimpel123", RoleEnum.gestor, "Gestor de Projetos")

            # ── Em andamento ──────────────────────────────────────────────────

            # Assaí - Sachê
            c = ["Sinal","Negociação","Formalização","Amostra"]
            add_projeto(db, cliente="Assaí", marca="A definir", produto="Lava Roupas", tipo_embalagem="Sachê", gramatura="2,4KG / 4KG", formulacao="PHX-Q700", tipo_contrato=TipoContratoEnum.full_service, tipo_projeto=TipoProjetoEnum.novo_produto, status=StatusProjetoEnum.em_andamento, gestao_externa="Virtuss Branding", etapa_atual="Embalagem EAN / DUN", progresso=calcular_progresso(c), etapas_c=c)

            # Assaí - Cartucho
            c = ["Sinal","Negociação"]
            add_projeto(db, cliente="Assaí", marca="A definir", produto="Lava Roupas", tipo_embalagem="Cartucho", gramatura="800G / 1,6KG", formulacao="PHX-Q700", tipo_contrato=TipoContratoEnum.full_service, tipo_projeto=TipoProjetoEnum.novo_produto, status=StatusProjetoEnum.em_andamento, gestao_externa="Virtuss Branding", etapa_atual="Formalização", progresso=calcular_progresso(c), etapas_c=c)

            # Clara
            c = ["Sinal","Negociação","Formalização","Amostra","Embalagem - Ficha Técnica","Embalagem - Planta Técnica","Embalagem - Dizeres de Rotulagem","Embalagem - Rotas Criativas","Embalagem - Planificação"]
            add_projeto(db, cliente="Clara", marca="Clara", produto="Lava Roupas", tipo_embalagem="Sachê", gramatura="1,4KG / 4KG", formulacao="PHX-Q350", tipo_contrato=TipoContratoEnum.full_service, tipo_projeto=TipoProjetoEnum.novo_produto, status=StatusProjetoEnum.em_andamento, gestao_externa="Amicci / Phoenix Brands", etapa_atual="Embalagem - Planificação", progresso=calcular_progresso(c), etapas_c=c)

            # Maxi Compras - Lava Roupas
            c = ["Sinal","Negociação"]
            add_projeto(db, cliente="Maxi Compras", marca="Maxi Casa", produto="Lava Roupas", tipo_embalagem="Sachê", gramatura="800G / 1,6KG / 2,4KG / 4KG", tipo_contrato=TipoContratoEnum.full_service, tipo_projeto=TipoProjetoEnum.novo_produto, status=StatusProjetoEnum.em_andamento, gestao_externa="Willian Gadelha", etapa_atual="Formalização", progresso=calcular_progresso(c), etapas_c=c)

            # Maxi Compras - Lava Roupas Coco
            c = ["Sinal","Negociação"]
            add_projeto(db, cliente="Maxi Compras", marca="Maxi Casa", produto="Lava Roupas Coco", tipo_embalagem="Sachê", gramatura="1KG", tipo_contrato=TipoContratoEnum.full_service, tipo_projeto=TipoProjetoEnum.novo_produto, status=StatusProjetoEnum.em_andamento, gestao_externa="Willian Gadelha", etapa_atual="Formalização", progresso=calcular_progresso(c), etapas_c=c)

            # Maxi Compras - Tira Manchas
            c = ["Sinal","Negociação"]
            add_projeto(db, cliente="Maxi Compras", marca="Maxi Casa", produto="Tira Manchas", tipo_embalagem="Sachê", gramatura="400G", tipo_contrato=TipoContratoEnum.full_service, tipo_projeto=TipoProjetoEnum.novo_produto, status=StatusProjetoEnum.em_andamento, gestao_externa="Willian Gadelha", etapa_atual="Formalização", progresso=calcular_progresso(c), etapas_c=c)

            # Muffato - Sachê
            c = ["Sinal","Negociação","Formalização","Amostra"]
            add_projeto(db, cliente="Muffato", marca="A definir", produto="Lava Roupas", tipo_embalagem="Sachê", tipo_contrato=TipoContratoEnum.full_service, tipo_projeto=TipoProjetoEnum.novo_produto, status=StatusProjetoEnum.em_andamento, gestao_externa="Willian Gadelha", etapa_atual="Embalagem EAN / DUN", progresso=calcular_progresso(c), etapas_c=c)

            # Muffato - Cartucho
            c = ["Sinal","Negociação","Formalização","Amostra"]
            add_projeto(db, cliente="Muffato", marca="A definir", produto="Lava Roupas", tipo_embalagem="Cartucho", tipo_contrato=TipoContratoEnum.full_service, tipo_projeto=TipoProjetoEnum.novo_produto, status=StatusProjetoEnum.em_andamento, gestao_externa="Willian Gadelha", etapa_atual="Embalagem EAN / DUN", progresso=calcular_progresso(c), etapas_c=c)

            # Plurix - Nida
            c = ["Sinal","Negociação","Formalização","Amostra"]
            add_projeto(db, cliente="Plurix", marca="Nida", produto="Lava Roupas", tipo_embalagem="Sachê", gramatura="1,6KG / 2,2KG", tipo_contrato=TipoContratoEnum.full_service, tipo_projeto=TipoProjetoEnum.novo_produto, status=StatusProjetoEnum.em_andamento, gestao_externa="Amicci / Phoenix Brands", etapa_atual="Amostra", progresso=calcular_progresso(c), etapas_c=c)

            # Prezunic - Home Care
            c = ["Sinal","Negociação","Formalização","Amostra"]
            add_projeto(db, cliente="Prezunic", marca="Home Care", produto="Lava Roupas", tipo_embalagem="Sachê", gramatura="1,6KG", formulacao="PHX-Q700", tipo_contrato=TipoContratoEnum.full_service, tipo_projeto=TipoProjetoEnum.novo_produto, status=StatusProjetoEnum.em_andamento, gestao_externa="Amicci / Phoenix Brands", etapa_atual="Amostra", progresso=calcular_progresso(c), etapas_c=c)

            # Raymundo da Fonte - Sachê
            add_projeto(db, cliente="Raymundo da Fonte", produto="Lava Roupas", tipo_embalagem="Sachê", tipo_contrato=TipoContratoEnum.servico, tipo_projeto=TipoProjetoEnum.novo_produto, status=StatusProjetoEnum.em_andamento, gestao_externa="Willian Gadelha", etapa_atual="Negociação", progresso=0.0, etapas_c=[])

            # Raymundo da Fonte - Cartucho
            add_projeto(db, cliente="Raymundo da Fonte", produto="Lava Roupas", tipo_embalagem="Cartucho", tipo_contrato=TipoContratoEnum.servico, tipo_projeto=TipoProjetoEnum.novo_produto, status=StatusProjetoEnum.em_andamento, gestao_externa="Willian Gadelha", etapa_atual="Negociação", progresso=0.0, etapas_c=[])

            # Raymundo da Fonte - Tira Manchas
            add_projeto(db, cliente="Raymundo da Fonte", produto="Tira Manchas", tipo_embalagem="Sachê", tipo_contrato=TipoContratoEnum.servico, tipo_projeto=TipoProjetoEnum.novo_produto, status=StatusProjetoEnum.em_andamento, gestao_externa="Willian Gadelha", etapa_atual="Negociação", progresso=0.0, etapas_c=[])

            # Rede ABC - Lava Roupas Coco
            c = ["Sinal","Negociação","Formalização","Amostra","Embalagem EAN / DUN","Embalagem - Ficha Técnica","Embalagem - Planta Técnica"]
            add_projeto(db, cliente="Rede ABC", marca="ABC", produto="Lava Roupas Coco", tipo_embalagem="Sachê", gramatura="1KG", formulacao="PHX-Q450", tipo_contrato=TipoContratoEnum.full_service, tipo_projeto=TipoProjetoEnum.novo_produto, status=StatusProjetoEnum.em_andamento, gestao_externa="Phoenix Brands", etapa_atual="Embalagem - Rotas Criativas", progresso=calcular_progresso(c), etapas_c=c)

            # Rede ABC - Tira Manchas
            c = ["Sinal","Negociação","Formalização","Amostra","Embalagem EAN / DUN","Embalagem - Ficha Técnica","Embalagem - Planta Técnica"]
            add_projeto(db, cliente="Rede ABC", marca="ABC", produto="Tira Manchas", tipo_embalagem="Sachê", gramatura="400G", formulacao="IMCD", tipo_contrato=TipoContratoEnum.full_service, tipo_projeto=TipoProjetoEnum.novo_produto, status=StatusProjetoEnum.em_andamento, gestao_externa="Phoenix Brands", etapa_atual="Embalagem - Rotas Criativas", progresso=calcular_progresso(c), etapas_c=c)

            # Rede ABC - Lava Roupas
            c = ["Sinal","Negociação","Formalização","Amostra","Embalagem EAN / DUN","Embalagem - Ficha Técnica","Embalagem - Planta Técnica","Embalagem - Dizeres de Rotulagem","Embalagem - Rotas Criativas","Embalagem - Planificação"]
            add_projeto(db, cliente="Rede ABC", marca="ABC", produto="Lava Roupas", tipo_embalagem="Sachê", gramatura="1,6KG / 4KG", formulacao="PHX-Q450", tipo_contrato=TipoContratoEnum.full_service, tipo_projeto=TipoProjetoEnum.novo_produto, status=StatusProjetoEnum.em_andamento, gestao_externa="Phoenix Brands", etapa_atual="Clicheria", progresso=calcular_progresso(c), etapas_c=c)

            # Rede Basil - Lava Roupas
            c = ["Sinal","Negociação"]
            add_projeto(db, cliente="Rede Basil", marca="Plin", produto="Lava Roupas", tipo_embalagem="Sachê", gramatura="800G / 1,6KG / 2,4KG / 4KG", tipo_contrato=TipoContratoEnum.full_service, tipo_projeto=TipoProjetoEnum.novo_produto, status=StatusProjetoEnum.em_andamento, gestao_externa="Willian Gadelha", etapa_atual="Formalização", progresso=calcular_progresso(c), etapas_c=c)

            # Rede Basil - Lava Roupas Coco
            c = ["Sinal","Negociação"]
            add_projeto(db, cliente="Rede Basil", marca="Plin", produto="Lava Roupas Coco", tipo_embalagem="Sachê", gramatura="1KG", tipo_contrato=TipoContratoEnum.full_service, tipo_projeto=TipoProjetoEnum.novo_produto, status=StatusProjetoEnum.em_andamento, gestao_externa="Willian Gadelha", etapa_atual="Formalização", progresso=calcular_progresso(c), etapas_c=c)

            # Rede Basil - Tira Manchas
            c = ["Sinal","Negociação"]
            add_projeto(db, cliente="Rede Basil", marca="Plin", produto="Tira Manchas", tipo_embalagem="Sachê", gramatura="400G", tipo_contrato=TipoContratoEnum.full_service, tipo_projeto=TipoProjetoEnum.novo_produto, status=StatusProjetoEnum.em_andamento, gestao_externa="Willian Gadelha", etapa_atual="Formalização", progresso=calcular_progresso(c), etapas_c=c)

            # Rede Unibrasil - Felitá Lava Roupas Coco
            c = ["Sinal","Negociação","Formalização","Amostra","Embalagem EAN / DUN","Embalagem - Ficha Técnica","Embalagem - Planta Técnica"]
            add_projeto(db, numero="31763", cliente="Rede Unibrasil", marca="Felitá", produto="Lava Roupas Coco", tipo_embalagem="Sachê", gramatura="1KG", formulacao="PHX-Q550", tipo_contrato=TipoContratoEnum.full_service, tipo_projeto=TipoProjetoEnum.novo_produto, status=StatusProjetoEnum.em_andamento, gestao_externa="Amicci / Phoenix Brands", etapa_atual="Embalagem - Rotas Criativas", progresso=calcular_progresso(c), etapas_c=c)

            # Rede Unibrasil - Felitá Tira Manchas
            c = ["Sinal","Negociação","Formalização","Amostra","Embalagem EAN / DUN","Embalagem - Ficha Técnica","Embalagem - Planta Técnica"]
            add_projeto(db, numero="31771", cliente="Rede Unibrasil", marca="Felitá", produto="Tira Manchas", tipo_embalagem="Sachê", gramatura="400G", formulacao="IMCD", tipo_contrato=TipoContratoEnum.full_service, tipo_projeto=TipoProjetoEnum.novo_produto, status=StatusProjetoEnum.em_andamento, gestao_externa="Amicci / Phoenix Brands", etapa_atual="Embalagem - Rotas Criativas", progresso=calcular_progresso(c), etapas_c=c)

            # Rede Unibrasil - Felitá Lava Roupas Cartucho (extensão de linha)
            c = ["Sinal","Negociação","Formalização","Amostra","Embalagem EAN / DUN","Embalagem - Ficha Técnica","Embalagem - Planta Técnica","Embalagem - Dizeres de Rotulagem","Embalagem - Rotas Criativas","Embalagem - Planificação"]
            add_projeto(db, numero="30138", cliente="Rede Unibrasil", marca="Felitá", produto="Lava Roupas", tipo_embalagem="Cartucho", gramatura="2,2KG", formulacao="PHQ-Q700", tipo_contrato=TipoContratoEnum.full_service, tipo_projeto=TipoProjetoEnum.extensao_linha, status=StatusProjetoEnum.em_andamento, gestao_externa="Amicci / Phoenix Brands", etapa_atual="Embalagem - Planificação", progresso=calcular_progresso(c), etapas_c=c)

            # Ypê - Lava Roupas Sachê
            add_projeto(db, cliente="Ypê", marca="Ypê", produto="Lava Roupas", tipo_embalagem="Sachê", tipo_contrato=TipoContratoEnum.servico, tipo_projeto=TipoProjetoEnum.novo_produto, status=StatusProjetoEnum.em_andamento, gestao_externa="Willian Gadelha", etapa_atual="Negociação", progresso=0.0, etapas_c=[])

            # Ypê - Lava Roupas Cartucho
            add_projeto(db, cliente="Ypê", marca="Ypê", produto="Lava Roupas", tipo_embalagem="Cartucho", tipo_contrato=TipoContratoEnum.servico, tipo_projeto=TipoProjetoEnum.novo_produto, status=StatusProjetoEnum.em_andamento, gestao_externa="Willian Gadelha", etapa_atual="Negociação", progresso=0.0, etapas_c=[])

            # Ypê - Lava Louças
            add_projeto(db, cliente="Ypê", marca="Ypê", produto="Lava Louças", tipo_embalagem="Sachê", tipo_contrato=TipoContratoEnum.servico, tipo_projeto=TipoProjetoEnum.novo_produto, status=StatusProjetoEnum.em_andamento, gestao_externa="Willian Gadelha", etapa_atual="Negociação", progresso=0.0, etapas_c=[])

            # Ypê - Tira Manchas
            add_projeto(db, cliente="Ypê", marca="Ypê", produto="Tira Manchas", tipo_embalagem="Sachê", tipo_contrato=TipoContratoEnum.servico, tipo_projeto=TipoProjetoEnum.novo_produto, status=StatusProjetoEnum.em_andamento, gestao_externa="Willian Gadelha", etapa_atual="Negociação", progresso=0.0, etapas_c=[])

            # ── Não iniciado ──────────────────────────────────────────────────
            add_projeto(db, cliente="Imec", produto="", tipo_contrato=TipoContratoEnum.full_service, tipo_projeto=TipoProjetoEnum.novo_produto, status=StatusProjetoEnum.nao_iniciado, etapa_atual="Sinal", progresso=0.0, etapas_c=[])

            # ── Concluídos ────────────────────────────────────────────────────
            todas = list(ETAPAS_PADRAO)

            add_projeto(db, cliente="Aromasil", marca="Aromasil", produto="Lava Roupas", tipo_embalagem="Sachê", gramatura="400G / 800G", formulacao="PHX-Q200", tipo_contrato=TipoContratoEnum.full_service, tipo_projeto=TipoProjetoEnum.novo_produto, status=StatusProjetoEnum.concluido, gestao_externa="Virtuss Branding", etapa_atual="Finalizado", progresso=1.0, etapas_c=todas)

            add_projeto(db, cliente="Cria Sim", marca="Amacitel", produto="Lava Roupas", tipo_embalagem="Sachê", gramatura="400G / 800G / 1,6KG / 2,4KG / 4KG", formulacao="PHX-Q540A / PHX-Q540T", tipo_contrato=TipoContratoEnum.servico, tipo_projeto=TipoProjetoEnum.novo_produto, status=StatusProjetoEnum.concluido, gestao_externa="Willian Gadelha", etapa_atual="Finalizado", progresso=1.0, etapas_c=todas)

            add_projeto(db, cliente="Kitlar", marca="Kitlar", produto="Lava Roupas", tipo_embalagem="Sachê", gramatura="800G", formulacao="PHX-Q350", tipo_contrato=TipoContratoEnum.full_service, tipo_projeto=TipoProjetoEnum.novo_produto, status=StatusProjetoEnum.concluido, gestao_externa="Willian Gadelha", etapa_atual="Finalizado", progresso=1.0, etapas_c=todas)

            add_projeto(db, cliente="Multishine", marca="Shine", produto="Lava Roupas", tipo_embalagem="Sachê", gramatura="4KG", formulacao="PHX-Q550", tipo_contrato=TipoContratoEnum.full_service, tipo_projeto=TipoProjetoEnum.novo_produto, status=StatusProjetoEnum.concluido, gestao_externa="Marcos Wichoski", etapa_atual="Finalizado", progresso=1.0, etapas_c=todas)

            add_projeto(db, numero="29388", cliente="Rede SP", marca="Unilimp", produto="Lava Roupas", tipo_embalagem="Sachê", gramatura="800G / 1,6KG", formulacao="PHX-Q450", tipo_contrato=TipoContratoEnum.full_service, tipo_projeto=TipoProjetoEnum.novo_produto, status=StatusProjetoEnum.concluido, gestao_externa="Amicci / Phoenix Brands", etapa_atual="Finalizado", progresso=1.0, etapas_c=todas)

            add_projeto(db, numero="19519", cliente="Rede Unibrasil", marca="Felitá", produto="Lava Roupas", tipo_embalagem="Sachê", gramatura="800G / 1,6KG", formulacao="PHX-Q550", tipo_contrato=TipoContratoEnum.full_service, tipo_projeto=TipoProjetoEnum.novo_produto, status=StatusProjetoEnum.concluido, gestao_externa="Amicci / Phoenix Brands", etapa_atual="Finalizado", progresso=1.0, etapas_c=todas)

            # ── Cancelado ─────────────────────────────────────────────────────
            add_projeto(db, cliente="Supernosso", marca="Apreço", produto="Lava Roupas", tipo_embalagem="Sachê", tipo_contrato=TipoContratoEnum.full_service, tipo_projeto=TipoProjetoEnum.novo_produto, status=StatusProjetoEnum.cancelado, etapa_atual="Cancelado", progresso=0.0, etapas_c=[])

            db.commit()
            print("Seed criado com sucesso! 35 projetos importados da planilha.")
        else:
            print("Dados já existem, seed ignorado.")
    except Exception as e:
        db.rollback()
        print(f"Erro no seed: {e}")
    finally:
        db.close()
    yield

app = FastAPI(title="Qualimpel P&D", description="Módulo de Projetos e Desenvolvimento", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(projetos.router)
app.include_router(dashboard.router)

if os.path.exists("frontend"):
    app.mount("/static", StaticFiles(directory="frontend"), name="static")

    @app.get("/", include_in_schema=False)
    def serve_frontend():
        return FileResponse("frontend/index.html")

    @app.get("/{full_path:path}", include_in_schema=False)
    def serve_spa(full_path: str):
        return FileResponse("frontend/index.html")
