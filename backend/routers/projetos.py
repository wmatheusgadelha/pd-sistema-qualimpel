from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from backend.core.database import get_db
from backend.core.security import get_current_user, require_gestor_or_admin
from backend.models.user import User, Projeto, EtapaProjeto, HistoricoEtapa, StatusEtapaEnum, StatusProjetoEnum
from backend.schemas.schemas import ProjetoCreate, ProjetoUpdate, ProjetoResponse, EtapaUpdate, HistoricoResponse

router = APIRouter(prefix="/api/projetos", tags=["Projetos P&D"])

# Etapas padrão do pipeline — na ordem da planilha
ETAPAS_PADRAO = [
    "Sinal",
    "Negociação",
    "Formalização",
    "Amostra",
    "Embalagem EAN / DUN",
    "Embalagem - Ficha Técnica",
    "Embalagem - Planta Técnica",
    "Embalagem - Dizeres de Rotulagem",
    "Embalagem - Rotas Criativas",
    "Embalagem - Planificação",
    "Embalagem - Caixa de Embarque",
    "Clicheria",
    "Embalagem - Impressão",
    "Produção",
]


def calcular_progresso(etapas: list) -> float:
    if not etapas:
        return 0.0
    concluidas = sum(1 for e in etapas if e.status == StatusEtapaEnum.concluido or e.status == "Concluído")
    nao_aplicaveis = sum(1 for e in etapas if e.status == StatusEtapaEnum.nao_aplicavel or e.status == "N/A")
    efetivas = len(etapas) - nao_aplicaveis
    if efetivas == 0:
        return 1.0
    return round(concluidas / len(etapas), 2)


def atualizar_etapa_atual(projeto: Projeto):
    proxima = None
    for etapa in sorted(projeto.etapas, key=lambda e: e.ordem):
        if etapa.status not in (StatusEtapaEnum.concluido, StatusEtapaEnum.nao_aplicavel):
            proxima = etapa.nome
            break
    projeto.etapa_atual = proxima or "Finalizado"
    projeto.progresso = calcular_progresso(projeto.etapas)

    # Atualizar status geral automaticamente
    todas_concluidas = all(
        e.status in (StatusEtapaEnum.concluido, StatusEtapaEnum.nao_aplicavel)
        for e in projeto.etapas
    )
    if todas_concluidas and projeto.etapas:
        projeto.status = StatusProjetoEnum.concluido
    elif any(e.status == StatusEtapaEnum.concluido for e in projeto.etapas):
        if projeto.status == StatusProjetoEnum.nao_iniciado:
            projeto.status = StatusProjetoEnum.em_andamento


@router.get("/", response_model=List[ProjetoResponse], summary="Listar projetos com filtros")
def listar_projetos(
    status: Optional[str] = Query(None),
    cliente: Optional[str] = Query(None),
    tipo_contrato: Optional[str] = Query(None),
    tipo_projeto: Optional[str] = Query(None),
    busca: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    q = db.query(Projeto).options(joinedload(Projeto.etapas))

    if status:
        q = q.filter(Projeto.status == status)
    if cliente:
        q = q.filter(Projeto.cliente.ilike(f"%{cliente}%"))
    if tipo_contrato:
        q = q.filter(Projeto.tipo_contrato == tipo_contrato)
    if tipo_projeto:
        q = q.filter(Projeto.tipo_projeto == tipo_projeto)
    if busca:
        q = q.filter(
            (Projeto.cliente.ilike(f"%{busca}%")) |
            (Projeto.produto.ilike(f"%{busca}%")) |
            (Projeto.marca.ilike(f"%{busca}%")) |
            (Projeto.numero.ilike(f"%{busca}%"))
        )

    return q.order_by(Projeto.cliente, Projeto.produto).all()


@router.get("/{projeto_id}", response_model=ProjetoResponse, summary="Detalhe de um projeto")
def detalhe_projeto(projeto_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    projeto = db.query(Projeto).options(joinedload(Projeto.etapas)).filter(Projeto.id == projeto_id).first()
    if not projeto:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")
    return projeto


@router.post("/", response_model=ProjetoResponse, summary="Criar novo projeto")
def criar_projeto(
    data: ProjetoCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_gestor_or_admin)
):
    projeto = Projeto(**data.model_dump())
    db.add(projeto)
    db.flush()  # obter ID antes de criar etapas

    # Criar etapas padrão
    for i, nome_etapa in enumerate(ETAPAS_PADRAO):
        etapa = EtapaProjeto(
            projeto_id=projeto.id,
            nome=nome_etapa,
            ordem=i + 1,
            status=StatusEtapaEnum.nao_iniciado,
        )
        db.add(etapa)

    db.flush()
    atualizar_etapa_atual(projeto)
    db.commit()
    db.refresh(projeto)
    return projeto


@router.put("/{projeto_id}", response_model=ProjetoResponse, summary="Editar projeto")
def editar_projeto(
    projeto_id: int,
    data: ProjetoUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_gestor_or_admin)
):
    projeto = db.query(Projeto).options(joinedload(Projeto.etapas)).filter(Projeto.id == projeto_id).first()
    if not projeto:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(projeto, field, value)
    db.commit()
    db.refresh(projeto)
    return projeto


@router.delete("/{projeto_id}", summary="Excluir projeto")
def excluir_projeto(projeto_id: int, db: Session = Depends(get_db), _=Depends(require_gestor_or_admin)):
    projeto = db.query(Projeto).filter(Projeto.id == projeto_id).first()
    if not projeto:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")
    db.delete(projeto)
    db.commit()
    return {"message": "Projeto excluído"}


# ─── Etapas ───────────────────────────────────────────────────────────────────

@router.put("/{projeto_id}/etapas/{etapa_id}", summary="Atualizar status de uma etapa")
def atualizar_etapa(
    projeto_id: int,
    etapa_id: int,
    data: EtapaUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    etapa = db.query(EtapaProjeto).filter(
        EtapaProjeto.id == etapa_id,
        EtapaProjeto.projeto_id == projeto_id
    ).first()
    if not etapa:
        raise HTTPException(status_code=404, detail="Etapa não encontrada")

    # Registrar histórico
    historico = HistoricoEtapa(
        projeto_id=projeto_id,
        etapa_nome=etapa.nome,
        status_anterior=etapa.status,
        status_novo=data.status,
        usuario_id=current_user.id,
        observacao=data.observacoes,
    )
    db.add(historico)

    # Atualizar etapa
    etapa.status = data.status
    if data.data_conclusao:
        etapa.data_conclusao = data.data_conclusao
    if data.responsavel_id is not None:
        etapa.responsavel_id = data.responsavel_id
    if data.observacoes is not None:
        etapa.observacoes = data.observacoes

    # Recalcular progresso
    projeto = db.query(Projeto).options(joinedload(Projeto.etapas)).filter(Projeto.id == projeto_id).first()
    atualizar_etapa_atual(projeto)

    db.commit()
    db.refresh(etapa)
    return {"message": "Etapa atualizada", "progresso": projeto.progresso, "etapa_atual": projeto.etapa_atual}


@router.get("/{projeto_id}/historico", response_model=List[HistoricoResponse], summary="Histórico de mudanças do projeto")
def historico_projeto(projeto_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    return db.query(HistoricoEtapa).filter(
        HistoricoEtapa.projeto_id == projeto_id
    ).order_by(HistoricoEtapa.data.desc()).all()
