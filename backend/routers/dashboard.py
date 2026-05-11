from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.core.database import get_db
from backend.core.security import get_current_user
from backend.models.user import User, Projeto, EtapaProjeto, StatusProjetoEnum

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/stats", summary="KPIs do dashboard P&D")
def dashboard_stats(db: Session = Depends(get_db), _=Depends(get_current_user)):
    total = db.query(Projeto).count()
    em_andamento = db.query(Projeto).filter(Projeto.status == StatusProjetoEnum.em_andamento).count()
    concluidos = db.query(Projeto).filter(Projeto.status == StatusProjetoEnum.concluido).count()
    nao_iniciados = db.query(Projeto).filter(Projeto.status == StatusProjetoEnum.nao_iniciado).count()
    cancelados = db.query(Projeto).filter(Projeto.status == StatusProjetoEnum.cancelado).count()

    # Por cliente
    por_cliente_raw = db.query(Projeto.cliente, func.count(Projeto.id)).group_by(Projeto.cliente).all()
    por_cliente = {row[0]: row[1] for row in por_cliente_raw}

    # Por tipo de contrato
    por_contrato_raw = db.query(Projeto.tipo_contrato, func.count(Projeto.id)).group_by(Projeto.tipo_contrato).all()
    por_contrato = {str(row[0].value if hasattr(row[0], 'value') else row[0]): row[1] for row in por_contrato_raw}

    # Por tipo de projeto
    por_tipo_raw = db.query(Projeto.tipo_projeto, func.count(Projeto.id)).group_by(Projeto.tipo_projeto).all()
    por_tipo = {str(row[0].value if hasattr(row[0], 'value') else row[0]): row[1] for row in por_tipo_raw}

    # Progresso médio
    prog_result = db.query(func.avg(Projeto.progresso)).scalar()
    progresso_medio = round(float(prog_result or 0) * 100, 1)

    # Etapas com mais projetos parados
    etapas_raw = (
        db.query(EtapaProjeto.nome, func.count(EtapaProjeto.id))
        .filter(EtapaProjeto.status == "Não iniciado")
        .group_by(EtapaProjeto.nome)
        .order_by(func.count(EtapaProjeto.id).desc())
        .limit(5)
        .all()
    )
    etapas_gargalo = {row[0]: row[1] for row in etapas_raw}

    # Projetos por etapa atual
    por_etapa_raw = db.query(Projeto.etapa_atual, func.count(Projeto.id)).group_by(Projeto.etapa_atual).all()
    por_etapa = {(row[0] or "Não definida"): row[1] for row in por_etapa_raw}

    return {
        "total_projetos": total,
        "em_andamento": em_andamento,
        "concluidos": concluidos,
        "nao_iniciados": nao_iniciados,
        "cancelados": cancelados,
        "por_cliente": por_cliente,
        "por_tipo_contrato": por_contrato,
        "por_tipo_projeto": por_tipo,
        "progresso_medio": progresso_medio,
        "etapas_gargalo": etapas_gargalo,
        "por_etapa_atual": por_etapa,
    }
