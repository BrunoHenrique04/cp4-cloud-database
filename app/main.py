"""API REST de Alunos - FastAPI + MongoDB (CP4 - Cloud Database)."""
from contextlib import asynccontextmanager

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pymongo.collection import Collection
from pymongo.errors import DuplicateKeyError

from app.database import get_collection, init_db
from app.schemas import AlunoCreate, AlunoResponse, AlunoUpdate, Mensagem


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="API de Alunos",
    description="CP4 - Cloud Database: CRUD de alunos com FastAPI e MongoDB.",
    version="1.0.0",
    lifespan=lifespan,
)


# ---------- helpers ----------
def to_response(doc: dict) -> AlunoResponse:
    return AlunoResponse(
        id=str(doc["_id"]),
        nome=doc["nome"],
        email=doc["email"],
        idade=doc["idade"],
        curso=doc["curso"],
    )


def parse_object_id(aluno_id: str) -> ObjectId:
    try:
        return ObjectId(aluno_id)
    except (InvalidId, TypeError):
        # ID em formato inválido também significa que o aluno não existe
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Aluno não encontrado")


def email_ja_cadastrado() -> HTTPException:
    return HTTPException(status.HTTP_409_CONFLICT, detail="Já existe um aluno cadastrado com este e-mail")


# ---------- tratamento de erros de validação ----------
@app.exception_handler(RequestValidationError)
async def validation_handler(_: Request, exc: RequestValidationError):
    erros = [
        {
            "campo": ".".join(str(p) for p in e["loc"] if p != "body"),
            "mensagem": e["msg"].replace("Value error, ", ""),
        }
        for e in exc.errors()
    ]
    return JSONResponse(
        status_code=422,
        content={"detail": "Erro de validação", "erros": erros},
    )


# ---------- endpoints ----------
@app.get("/", tags=["Health"])
def raiz():
    return {"status": "ok", "docs": "/docs"}


@app.post("/alunos", response_model=Mensagem, status_code=status.HTTP_201_CREATED, tags=["Alunos"])
def cadastrar_aluno(aluno: AlunoCreate, col: Collection = Depends(get_collection)):
    if col.find_one({"email": aluno.email}):
        raise email_ja_cadastrado()
    doc = aluno.model_dump()
    try:
        resultado = col.insert_one(doc)
    except DuplicateKeyError:
        raise email_ja_cadastrado()
    doc["_id"] = resultado.inserted_id
    return Mensagem(mensagem="Aluno cadastrado com sucesso", aluno=to_response(doc))


@app.get("/alunos", response_model=list[AlunoResponse], tags=["Alunos"])
def listar_alunos(col: Collection = Depends(get_collection)):
    return [to_response(doc) for doc in col.find()]


@app.get("/alunos/{id}", response_model=AlunoResponse, tags=["Alunos"])
def consultar_aluno(id: str, col: Collection = Depends(get_collection)):
    doc = col.find_one({"_id": parse_object_id(id)})
    if not doc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Aluno não encontrado")
    return to_response(doc)


@app.put("/alunos/{id}", response_model=Mensagem, tags=["Alunos"])
def atualizar_aluno(id: str, aluno: AlunoUpdate, col: Collection = Depends(get_collection)):
    oid = parse_object_id(id)
    if not col.find_one({"_id": oid}):
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Aluno não encontrado")
    if col.find_one({"email": aluno.email, "_id": {"$ne": oid}}):
        raise email_ja_cadastrado()
    try:
        col.update_one({"_id": oid}, {"$set": aluno.model_dump()})
    except DuplicateKeyError:
        raise email_ja_cadastrado()
    return Mensagem(mensagem="Aluno atualizado com sucesso", aluno=to_response(col.find_one({"_id": oid})))


@app.delete("/alunos/{id}", response_model=Mensagem, tags=["Alunos"])
def excluir_aluno(id: str, col: Collection = Depends(get_collection)):
    resultado = col.delete_one({"_id": parse_object_id(id)})
    if resultado.deleted_count == 0:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Aluno não encontrado")
    return Mensagem(mensagem="Aluno removido com sucesso")
