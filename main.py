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

def criar_etapas(db, projeto_id, etapas_concluidas=None):
    etapas_concluidas = etapas_concluidas or []
    for i, nome in enumerate(ETAPAS_PADRAO):
        status = StatusEtapaEnum.concluido if nome in etapas_concluidas else StatusEtapaEnum.nao_iniciado
        db.add(EtapaProjeto(
            projeto_id=projeto_id, nome=nome, ordem=i+1, status=status,
            data_conclusao=date(2025, 1, 15) if status == StatusEtapaEnum.concluido else None,
        ))

def calcular_progresso_seed(etapas_concluidas):
    return round(len(etapas_concluidas) / len(ETAPAS_PADRAO), 2)

def get_or_create_user(db, email, nome, senha, role, cargo):
    u = db.query(User).filter(User.email == email).first()
    if not u:
        u = User(nome=nome, email=email, hashed_password=get_password_hash(senha),
                 role=role, cargo=cargo, is_active=True)
        db.add(u)
        db.flush()
    return u

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
            admin = get_or_create_user(db, "admin@pd.com", "Administrador", "admin123", RoleEnum.admin, "Administrador do Sistema")
            willian = get_or_create_user(db, "willian@qualimpel.com", "Willian Gadelha", "qualimpel123", RoleEnum.gestor, "Gestor de P&D")
            marcos = get_or_create_user(db, "marcos@qualimpel.com", "Marcos Wichoski", "qualimpel123", RoleEnum.gestor, "Gestor de Projetos")

            conc_abc_lv = ["Sinal","Negociação","Formalização","Amostra","Embalagem EAN / DUN","Embalagem - Ficha Técnica","Embalagem - Planta Técnica","Embalagem - Dizeres de Rotulagem","Embalagem - Rotas Criativas","Embalagem - Planificação"]
            p1 = Projeto(cliente="Rede ABC", marca="ABC", produto="Lava Roupas", tipo_embalagem="Sachê", gramatura="1,6KG / 4KG", formulacao="PHX-Q450", tipo_contrato=TipoContratoEnum.full_service, tipo_projeto=TipoProjetoEnum.novo_produto, status=StatusProjetoEnum.em_andamento, gestor_id=willian.id, etapa_atual="Clicheria", progresso=calcular_progresso_seed(conc_abc_lv))
            db.add(p1); db.flush(); criar_etapas(db, p1.id, conc_abc_lv)

            conc_abc_coco = ["Sinal","Negociação","Formalização","Amostra","Embalagem EAN / DUN","Embalagem - Ficha Técnica","Embalagem - Planta Técnica"]
            p2 = Projeto(cliente="Rede ABC", marca="ABC", produto="Lava Roupas Coco", tipo_embalagem="Sachê", gramatura="1KG", formulacao="PHX-Q450", tipo_contrato=TipoContratoEnum.full_service, tipo_projeto=TipoProjetoEnum.novo_produto, status=StatusProjetoEnum.em_andamento, gestor_id=willian.id, etapa_atual="Embalagem - Dizeres de Rotulagem", progresso=calcular_progresso_seed(conc_abc_coco))
            db.add(p2); db.flush(); criar_etapas(db, p2.id, conc_abc_coco)

            conc_clara = ["Sinal","Negociação","Formalização","Amostra","Embalagem EAN / DUN","Embalagem - Ficha Técnica","Embalagem - Planta Técnica","Embalagem - Dizeres de Rotulagem","Embalagem - Rotas Criativas"]
            p3 = Projeto(cliente="Clara", marca="Clara", produto="Lava Roupas", tipo_embalagem="Sachê", gramatura="1,4KG / 4KG", formulacao="PHX-Q350", tipo_contrato=TipoContratoEnum.full_service, tipo_projeto=TipoProjetoEnum.novo_produto, status=StatusProjetoEnum.em_andamento, gestao_externa="Amicci / Phoenix Brands", etapa_atual="Embalagem - Planificação", progresso=calcular_progresso_seed(conc_clara))
            db.add(p3); db.flush(); criar_etapas(db, p3.id, conc_clara)

            conc_uni = ["Sinal","Negociação","Formalização","Amostra","Embalagem EAN / DUN","Embalagem - Ficha Técnica","Embalagem - Planta Técnica","Embalagem - Dizeres de Rotulagem","Embalagem - Rotas Criativas","Embalagem - Planificação"]
            p4 = Projeto(numero="30138", cliente="Rede Unibrasil", marca="Felitá", produto="Lava Roupas", tipo_embalagem="Cartucho", gramatura="2,2KG", formulacao="PHQ-Q700", tipo_contrato=TipoContratoEnum.full_service, tipo_projeto=TipoProjetoEnum.extensao_linha, status=StatusProjetoEnum.em_andamento, gestao_externa="Amicci / Phoenix Brands", etapa_atual="Embalagem - Caixa de Embarque", progresso=calcular_progresso_seed(conc_uni))
            db.add(p4); db.flush(); criar_etapas(db, p4.id, conc_uni)

            conc_assai = ["Sinal","Negociação","Formalização","Amostra"]
            p5 = Projeto(cliente="Assaí", produto="Lava Roupas", tipo_embalagem="Sachê", gramatura="2,4KG / 4KG", formulacao="PHX-Q700", tipo_contrato=TipoContratoEnum.full_service, tipo_projeto=TipoProjetoEnum.novo_produto, status=StatusProjetoEnum.em_andamento, gestao_externa="Virtuss Branding", etapa_atual="Embalagem EAN / DUN", progresso=calcular_progresso_seed(conc_assai))
            db.add(p5); db.flush(); criar_etapas(db, p5.id, conc_assai)

            p6 = Projeto(cliente="Ypê", marca="Ypê", produto="Lava Roupas", tipo_embalagem="Sachê", tipo_contrato=TipoContratoEnum.servico, tipo_projeto=TipoProjetoEnum.novo_produto, status=StatusProjetoEnum.em_andamento, gestor_id=willian.id, etapa_atual="Negociação", progresso=0.0)
            db.add(p6); db.flush(); criar_etapas(db, p6.id, ["Sinal"])

            p7 = Projeto(cliente="Maxi Compras", marca="Maxi Casa", produto="Lava Roupas", tipo_embalagem="Sachê", gramatura="800G / 1,6KG / 2,4KG / 4KG", tipo_contrato=TipoContratoEnum.full_service, tipo_projeto=TipoProjetoEnum.novo_produto, status=StatusProjetoEnum.em_andamento, gestor_id=willian.id, etapa_atual="Formalização", progresso=0.08)
            db.add(p7); db.flush(); criar_etapas(db, p7.id, ["Sinal","Negociação"])

            todas = list(ETAPAS_PADRAO)
            p8 = Projeto(numero="19519", cliente="Rede Unibrasil", marca="Felitá", produto="Lava Roupas", tipo_embalagem="Sachê", gramatura="800G / 1,6KG", formulacao="PHX-Q550", tipo_contrato=TipoContratoEnum.full_service, tipo_projeto=TipoProjetoEnum.novo_produto, status=StatusProjetoEnum.concluido, gestao_externa="Amicci / Phoenix Brands", etapa_atual="Finalizado", progresso=1.0)
            db.add(p8); db.flush(); criar_etapas(db, p8.id, todas)

            p9 = Projeto(numero="29388", cliente="Rede SP", marca="Unilimp", produto="Lava Roupas", tipo_embalagem="Sachê", gramatura="800G / 1,6KG", formulacao="PHX-Q450", tipo_contrato=TipoContratoEnum.full_service, tipo_projeto=TipoProjetoEnum.novo_produto, status=StatusProjetoEnum.concluido, gestao_externa="Amicci / Phoenix Brands", etapa_atual="Finalizado", progresso=1.0)
            db.add(p9); db.flush(); criar_etapas(db, p9.id, todas)

            p10 = Projeto(cliente="Aromasil", marca="Aromasil", produto="Lava Roupas", tipo_embalagem="Sachê", gramatura="400G / 800G", formulacao="PHX-Q200", tipo_contrato=TipoContratoEnum.full_service, tipo_projeto=TipoProjetoEnum.novo_produto, status=StatusProjetoEnum.concluido, gestao_externa="Virtuss Branding", etapa_atual="Finalizado", progresso=1.0)
            db.add(p10); db.flush(); criar_etapas(db, p10.id, todas)

            p11 = Projeto(cliente="Supernosso", marca="Apreço", produto="Lava Roupas", tipo_embalagem="Sachê", tipo_contrato=TipoContratoEnum.full_service, tipo_projeto=TipoProjetoEnum.novo_produto, status=StatusProjetoEnum.cancelado, etapa_atual="Cancelado", progresso=0.0)
            db.add(p11); db.flush(); criar_etapas(db, p11.id, [])

            db.commit()
            print("Seed criado com sucesso!")
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
