from datetime import datetime, timezone
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from .database import Base, engine, get_db
from . import models, schemas
from .security import hash_password, verify_password, create_access_token
from .dependencies import get_current_user, require_roles
from sqlalchemy import text
from .database import engine


Base.metadata.create_all(bind=engine)
app = FastAPI(title="Almoxarifado API", version="1.0.0")

@app.get("/")
def inicio():
    return {"mensagem": "API do Almoxarifado funcionando", "documentacao": "/docs"}

@app.on_event("startup")
def criar_admin_inicial():
    db = next(get_db())
    try:
        admin = db.query(models.Usuario).filter(models.Usuario.email == "admin@almox.local").first()
        if not admin:
            db.add(models.Usuario(
                nome="Administrador inicial",
                email="admin@almox.local",
                senha_hash=hash_password("Admin123!"),
                papel="administrador",
            ))
            db.commit()
    finally:
        db.close()

@app.post("/auth/login", response_model=schemas.TokenOut)
def login(dados: schemas.LoginIn, db: Session = Depends(get_db)):
    usuario = db.query(models.Usuario).filter(models.Usuario.email == dados.email).first()
    if not usuario or not verify_password(dados.senha, usuario.senha_hash):
        raise HTTPException(status_code=401, detail="E-mail ou senha incorretos")
    token = create_access_token(str(usuario.id), usuario.papel)
    return {"access_token": token, "token_type": "bearer"}

@app.get("/auth/me", response_model=schemas.UsuarioOut)
def meu_usuario(usuario=Depends(get_current_user)):
    return usuario

@app.post("/usuarios", response_model=schemas.UsuarioOut, status_code=201)
def criar_usuario(
    dados: schemas.UsuarioCreate,
    db: Session = Depends(get_db),
    admin=Depends(require_roles("administrador")),
):
    if dados.papel not in ("comum", "gestor", "administrador"):
        raise HTTPException(status_code=422, detail="Papel inválido")
    usuario = models.Usuario(
        nome=dados.nome, email=dados.email,
        senha_hash=hash_password(dados.senha), papel=dados.papel
    )
    db.add(usuario)
    try:
        db.commit()
        db.refresh(usuario)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Já existe usuário com este e-mail")
    return usuario

@app.get("/equipamentos", response_model=list[schemas.EquipamentoOut])
def listar_equipamentos(db: Session = Depends(get_db), usuario=Depends(get_current_user)):
    return db.query(models.Equipamento).order_by(models.Equipamento.id).all()

@app.post("/equipamentos", response_model=schemas.EquipamentoOut, status_code=201)
def cadastrar_equipamento(
    dados: schemas.EquipamentoCreate,
    db: Session = Depends(get_db),
    admin=Depends(require_roles("administrador")),
):
    equipamento = models.Equipamento(**dados.model_dump())
    db.add(equipamento)
    try:
        db.commit()
        db.refresh(equipamento)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Patrimônio já cadastrado")
    return equipamento

@app.post("/emprestimos", response_model=schemas.EmprestimoOut, status_code=201)
def solicitar_emprestimo(
    dados: schemas.EmprestimoCreate,
    db: Session = Depends(get_db),
    usuario=Depends(require_roles("comum")),
):
    equipamento = db.query(models.Equipamento).filter(models.Equipamento.id == dados.equipamento_id).first()
    if not equipamento:
        raise HTTPException(status_code=404, detail="Equipamento não encontrado")
    if not equipamento.disponivel:
        raise HTTPException(status_code=409, detail="Equipamento indisponível")
    emprestimo = models.Emprestimo(usuario_id=usuario.id, equipamento_id=equipamento.id, status="solicitado")
    db.add(emprestimo)
    db.commit()
    db.refresh(emprestimo)
    return emprestimo

@app.get("/emprestimos")
def listar_emprestimos(
    db: Session = Depends(get_db),
    usuario=Depends(get_current_user),
):
    query = db.query(models.Emprestimo)
    if usuario.papel == "comum":
        query = query.filter(models.Emprestimo.usuario_id == usuario.id)
    return [
        {
            "id": e.id, "usuario_id": e.usuario_id, "equipamento_id": e.equipamento_id,
            "status": e.status, "solicitado_em": e.solicitado_em,
            "aprovado_por": e.aprovado_por, "aprovado_em": e.aprovado_em,
            "devolvido_por": e.devolvido_por, "devolvido_em": e.devolvido_em,
        }
        for e in query.order_by(models.Emprestimo.id.desc()).all()
    ]

@app.post("/emprestimos/{emprestimo_id}/aprovar", response_model=schemas.EmprestimoOut)
def aprovar_emprestimo(
    emprestimo_id: int,
    db: Session = Depends(get_db),
    gestor=Depends(require_roles("gestor")),
):
    emprestimo = db.query(models.Emprestimo).filter(models.Emprestimo.id == emprestimo_id).first()
    if not emprestimo:
        raise HTTPException(status_code=404, detail="Empréstimo não encontrado")
    if emprestimo.status != "solicitado":
        raise HTTPException(status_code=409, detail="Empréstimo não está aguardando aprovação")
    equipamento = db.query(models.Equipamento).filter(models.Equipamento.id == emprestimo.equipamento_id).first()
    if not equipamento or not equipamento.disponivel:
        raise HTTPException(status_code=409, detail="Equipamento indisponível")
    equipamento.disponivel = False
    emprestimo.status = "aprovado"
    emprestimo.aprovado_por = gestor.id
    emprestimo.aprovado_em = datetime.now(timezone.utc)
    db.commit()
    db.refresh(emprestimo)
    return emprestimo

@app.post("/emprestimos/{emprestimo_id}/devolver", response_model=schemas.EmprestimoOut)
def registrar_devolucao(
    emprestimo_id: int,
    db: Session = Depends(get_db),
    gestor=Depends(require_roles("gestor")),
):
    emprestimo = db.query(models.Emprestimo).filter(models.Emprestimo.id == emprestimo_id).first()
    if not emprestimo:
        raise HTTPException(status_code=404, detail="Empréstimo não encontrado")
    if emprestimo.status != "aprovado":
        raise HTTPException(status_code=409, detail="Só é possível devolver empréstimos aprovados")
    equipamento = db.query(models.Equipamento).filter(models.Equipamento.id == emprestimo.equipamento_id).first()
    equipamento.disponivel = True
    emprestimo.status = "devolvido"
    emprestimo.devolvido_por = gestor.id
    emprestimo.devolvido_em = datetime.now(timezone.utc)
    db.commit()
    db.refresh(emprestimo)
    return emprestimo


@app.on_event("startup")
def criar_admin_inicial():
    db = next(get_db())
    try:
        admin = db.query(models.Usuario).filter(
            models.Usuario.email == "admin@almox.com"
        ).first()

        if not admin:
            novo_admin = models.Usuario(
                nome="Administrador inicial",
                email="admin@almox.com",
                senha_hash=hash_password("Admin123!"),
                papel="administrador",
            )
            db.add(novo_admin)
            db.commit()
    finally:
        db.close()


@app.get("/diagnostico/banco")
def diagnostico_banco():
    with engine.connect() as conexao:
        resultado = conexao.execute(
            text("SELECT DATABASE()")
        ).scalar()

    return {"banco_conectado": resultado}