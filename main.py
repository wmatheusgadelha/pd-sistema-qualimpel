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


# ─── Etapas padrão ────────────────────────────────────────────────────────────

ETAPAS_PADRAO = [
    "Sinal", "Negociação", "Formalização", "Amostra",
    "Embalagem EAN / DUN", "Embalagem - Ficha Técnica",
    "Embalagem - Planta Técnica", "Embalagem - Dizeres de Rotulagem",
    "Embalagem - Rotas Criativas", "Embalagem - Planificação",
    "Embalagem - Caixa de Embarque", "Clicheria",
    "Embalagem - Impressão", "Produção",
]


def criar_etapas(db, projeto_id: int, etapas_concluidas: list = None):
    etapas_concluidas = etapas_concluidas or []
    for i, nome in enumerate(ETAPAS_PADRAO):
        status = StatusEtapaEnum.concluido if nome in etapas_concluidas else StatusEtapaEnum.nao_iniciado
        etapa = EtapaProjeto(
            projeto_id=projeto_id,
            nome=nome,
            ordem=i + 1,
            status=status,
            data_conclusao=date(2025, 1, 15) if status == StatusEtapaEnum.concluido else None,
        )
        db.add(etapa)


def calcular_progresso_seed(etapas_concluidas: list) -> float:
    return round(len(etapas_concluidas) / len(ETAPAS_PADRAO), 2)


def etapa_atual_seed(etapas_concluidas: list) -> str:
    for etapa in ETAPAS_PADRAO:
        if etapa not in etapas_concluidas:
            return etapa
    return "Finalizado"


# ─── Lifespan (seed) ──────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        reset_seed = os.getenv("RESET_SEED", "false").lower() == "true"
        pd_admin_existe = db.query(User).filter(User.email == "admin@pd.com").first()
        if not pd_admin_existe or reset_seed:
            # Usuários
            admin = User(
                nome="Administrador", email="admin@pd.com",
                hashed_password=get_password_hash("admin123"),
                role=RoleEnum.admin, cargo="Administrador do Sistema", is_active=True
            )
            willian = User(
                nome="Willian Gadelha", email="willian@qualimpel.com",
                hashed_password=get_password_hash("qualimpel123"),
                role=RoleEnum.gestor, cargo="Gestor de P&D", is_active=True
            )
            marcos = User(
                nome="Marcos Wichoski", email="marcos@qualimpel.com",
                hashed_password=get_password_hash("qualimpel123"),
                role=RoleEnum.gestor, cargo="Gestor de Projetos", is_active=True
            )
            db.add_all([admin, willian, marcos])
            db.flush()

            # ── Projetos em andamento ──────────────────────────────────────

            # Rede ABC - Lava Roupas (mais avançado)
            conc_abc_lv = ["Sinal", "Negociação", "Formalização", "Amostra",
                           "Embalagem EAN / DUN", "Embalagem - Ficha Técnica",
                           "Embalagem - Planta Técnica", "Embalagem - Dizeres de Rotulagem",
                           "Embalagem - Rotas Criativas", "Embalagem - Planificação"]
            p1 = Projeto(
                cliente="Rede ABC", marca="ABC", produto="Lava Roupas",
                tipo_embalagem="Sachê", gramatura="1,6KG / 4KG", formulacao="PHX-Q450",
                tipo_contrato=TipoContratoEnum.full_service, tipo_projeto=TipoProjetoEnum.novo_produto,
                status=StatusProjetoEnum.em_andamento, gestor_id=willian.id,
                etapa_atual="Clicheria", progresso=calcular_progresso_seed(conc_abc_lv),
            )
            db.add(p1); db.flush()
            criar_etapas(db, p1.id, conc_abc_lv)

            # Rede ABC - Lava Roupas Coco
            conc_abc_coco = ["Sinal", "Negociação", "Formalização", "Amostra",
                             "Embalagem EAN / DUN", "Embalagem - Ficha Técnica",
                             "Embalagem - Planta Técnica"]
            p2 = Projeto(
                cliente="Rede ABC", marca="ABC", produto="Lava Roupas Coco",
                tipo_embalagem="Sachê", gramatura="1KG", formulacao="PHX-Q450",
                tipo_contrato=TipoContratoEnum.full_service, tipo_projeto=TipoProjetoEnum.novo_produto,
                status=StatusProjetoEnum.em_andamento, gestor_id=willian.id,
                etapa_atual="Embalagem - Dizeres de Rotulagem",
                progresso=calcular_progresso_seed(conc_abc_coco),
            )
            db.add(p2); db.flush()
            criar_etapas(db, p2.id, conc_abc_coco)

            # Clara - Lava Roupas
            conc_clara = ["Sinal", "Negociação", "Formalização", "Amostra",
                          "Embalagem EAN / DUN", "Embalagem - Ficha Técnica",
                          "Embalagem - Planta Técnica", "Embalagem - Dizeres de Rotulagem",
                          "Embalagem - Rotas Criativas"]
            p3 = Projeto(
                cliente="Clara", marca="Clara", produto="Lava Roupas",
                tipo_embalagem="Sachê", gramatura="1,4KG / 4KG", formulacao="PHX-Q350",
                tipo_contrato=TipoContratoEnum.full_service, tipo_projeto=TipoProjetoEnum.novo_produto,
                status=StatusProjetoEnum.em_andamento,
                gestao_externa="Amicci / Phoenix Brands",
                etapa_atual="Embalagem - Planificação",
                progresso=calcular_progresso_seed(conc_clara),
            )
            db.add(p3); db.flush()
            criar_etapas(db, p3.id, conc_clara)

            # Rede Unibrasil - Felitá Lava Roupas (extensão de linha avançada)
            conc_uni = ["Sinal", "Negociação", "Formalização", "Amostra",
                        "Embalagem EAN / DUN", "Embalagem - Ficha Técnica",
                        "Embalagem - Planta Técnica", "Embalagem - Dizeres de Rotulagem",
                        "Embalagem - Rotas Criativas", "Embalagem - Planificação"]
            p4 = Projeto(
                numero="30138", cliente="Rede Unibrasil", marca="Felitá", produto="Lava Roupas",
                tipo_embalagem="Cartucho", gramatura="2,2KG", formulacao="PHQ-Q700",
                tipo_contrato=TipoContratoEnum.full_service, tipo_projeto=TipoProjetoEnum.extensao_linha,
                status=StatusProjetoEnum.em_andamento,
                gestao_externa="Amicci / Phoenix Brands",
                etapa_atual="Embalagem - Caixa de Embarque",
                progresso=calcular_progresso_seed(conc_uni),
            )
            db.add(p4); db.flush()
            criar_etapas(db, p4.id, conc_uni)

            # Assaí - Lava Roupas Sachê
            conc_assai = ["Sinal", "Negociação", "Formalização", "Amostra"]
            p5 = Projeto(
                cliente="Assaí", produto="Lava Roupas",
                tipo_embalagem="Sachê", gramatura="2,4KG / 4KG", formulacao="PHX-Q700",
                tipo_contrato=TipoContratoEnum.full_service, tipo_projeto=TipoProjetoEnum.novo_produto,
                status=StatusProjetoEnum.em_andamento,
                gestao_externa="Virtuss Branding",
                etapa_atual="Embalagem EAN / DUN",
                progresso=calcular_progresso_seed(conc_assai),
            )
            db.add(p5); db.flush()
            criar_etapas(db, p5.id, conc_assai)

            # Ypê - em negociação
            p6 = Projeto(
                cliente="Ypê", marca="Ypê", produto="Lava Roupas",
                tipo_embalagem="Sachê", tipo_contrato=TipoContratoEnum.servico,
                tipo_projeto=TipoProjetoEnum.novo_produto,
                status=StatusProjetoEnum.em_andamento, gestor_id=willian.id,
                etapa_atual="Negociação", progresso=0.0,
            )
            db.add(p6); db.flush()
            criar_etapas(db, p6.id, ["Sinal"])

            # Maxi Compras - não iniciado
            p7 = Projeto(
                cliente="Maxi Compras", marca="Maxi Casa", produto="Lava Roupas",
                tipo_embalagem="Sachê", gramatura="800G / 1,6KG / 2,4KG / 4KG",
                tipo_contrato=TipoContratoEnum.full_service, tipo_projeto=TipoProjetoEnum.novo_produto,
                status=StatusProjetoEnum.em_andamento, gestor_id=willian.id,
                etapa_atual="Formalização", progresso=0.08,
            )
            db.add(p7); db.flush()
            criar_etapas(db, p7.id, ["Sinal", "Negociação"])

            # ── Projetos concluídos ──────────────────────────────────────

            todas = list(ETAPAS_PADRAO)
            p8 = Projeto(
                numero="19519", cliente="Rede Unibrasil", marca="Felitá", produto="Lava Roupas",
                tipo_embalagem="Sachê", gramatura="800G / 1,6KG", formulacao="PHX-Q550",
                tipo_contrato=TipoContratoEnum.full_service, tipo_projeto=TipoProjetoEnum.novo_produto,
                status=StatusProjetoEnum.concluido, gestao_externa="Amicci / Phoenix Brands",
                etapa_atual="Finalizado", progresso=1.0,
            )
            db.add(p8); db.flush()
            criar_etapas(db, p8.id, todas)

            p9 = Projeto(
                numero="29388", cliente="Rede SP", marca="Unilimp", produto="Lava Roupas",
                tipo_embalagem="Sachê", gramatura="800G / 1,6KG", formulacao="PHX-Q450",
                tipo_contrato=TipoContratoEnum.full_service, tipo_projeto=TipoProjetoEnum.novo_produto,
                status=StatusProjetoEnum.concluido, gestao_externa="Amicci / Phoenix Brands",
                etapa_atual="Finalizado", progresso=1.0,
            )
            db.add(p9); db.flush()
            criar_etapas(db, p9.id, todas)

            p10 = Projeto(
                cliente="Aromasil", marca="Aromasil", produto="Lava Roupas",
                tipo_embalagem="Sachê", gramatura="400G / 800G", formulacao="PHX-Q200",
                tipo_contrato=TipoContratoEnum.full_service, tipo_projeto=TipoProjetoEnum.novo_produto,
                status=StatusProjetoEnum.concluido, gestao_externa="Virtuss Branding",
                etapa_atual="Finalizado", progresso=1.0,
            )
            db.add(p10); db.flush()
            criar_etapas(db, p10.id, todas)

            # ── Cancelado ─────────────────────────────────────────────────

            p11 = Projeto(
                cliente="Supernosso", marca="Apreço", produto="Lava Roupas",
                tipo_embalagem="Sachê", tipo_contrato=TipoContratoEnum.full_service,
                tipo_projeto=TipoProjetoEnum.novo_produto,
                status=StatusProjetoEnum.cancelado,
                etapa_atual="Cancelado", progresso=0.0,
            )
            db.add(p11); db.flush()
            criar_etapas(db, p11.id, [])

            db.commit()
            print("✅ Seed de dados criado com sucesso!")
    except Exception as e:
        db.rollback()
        print(f"⚠️ Erro no seed: {e}")
    finally:
        db.close()
    yield


# ─── App ──────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Qualimpel P&D — Sistema de Projetos",
    description="Módulo de Projetos e Desenvolvimento da Qualimpel Indústria Química",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(projetos.router)
app.include_router(dashboard.router)

# Frontend estático
if os.path.exists("frontend"):
    app.mount("/static", StaticFiles(directory="frontend"), name="static")

    @app.get("/", include_in_schema=False)
    def serve_frontend():
        return FileResponse("frontend/index.html")

    @app.get("/{full_path:path}", include_in_schema=False)
    def serve_spa(full_path: str):
        return FileResponse("frontend/index.html")
