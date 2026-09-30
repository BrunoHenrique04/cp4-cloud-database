"""Testes automatizados (usam mongomock, não precisam de MongoDB rodando).

Executar: pytest -q
"""
import mongomock
import pytest
from fastapi.testclient import TestClient

from app import database
from app.main import app

JOAO = {"nome": "João Silva", "email": "joao@email.com", "idade": 22, "curso": "Ciência da Computação"}
MARIA = {"nome": "Maria Santos", "email": "maria@email.com", "idade": 24, "curso": "Engenharia de Software"}


@pytest.fixture
def client(monkeypatch):
    database._client = mongomock.MongoClient()
    with TestClient(app) as c:
        yield c
    database._client = None


def test_crud_completo(client):
    r = client.post("/alunos", json=JOAO)
    assert r.status_code == 201
    aluno_id = r.json()["aluno"]["id"]
    client.post("/alunos", json=MARIA)

    lista = client.get("/alunos").json()
    assert len(lista) == 2 and {"id", "nome", "email", "idade", "curso"} <= lista[0].keys()

    assert client.get(f"/alunos/{aluno_id}").json()["nome"] == "João Silva"

    novo = {"nome": "João da Silva", "email": "joao.silva@email.com", "idade": 23, "curso": "Engenharia de Software"}
    r = client.put(f"/alunos/{aluno_id}", json=novo)
    assert r.status_code == 200 and r.json()["aluno"]["curso"] == "Engenharia de Software"

    assert client.delete(f"/alunos/{aluno_id}").status_code == 200
    assert client.get(f"/alunos/{aluno_id}").status_code == 404
    assert client.delete(f"/alunos/{aluno_id}").status_code == 404


def test_requisicao_invalida(client):
    r = client.post("/alunos", json={"nome": "", "email": "email_invalido", "idade": 12, "curso": ""})
    assert r.status_code == 422
    campos = {e["campo"] for e in r.json()["erros"]}
    assert campos == {"nome", "email", "idade", "curso"}


def test_email_duplicado(client):
    assert client.post("/alunos", json=JOAO).status_code == 201
    r = client.post("/alunos", json={**MARIA, "email": "JOAO@email.com"})
    assert r.status_code == 409


def test_put_email_de_outro_aluno(client):
    client.post("/alunos", json=JOAO)
    maria_id = client.post("/alunos", json=MARIA).json()["aluno"]["id"]
    assert client.put(f"/alunos/{maria_id}", json={**MARIA, "email": "joao@email.com"}).status_code == 409


def test_id_inexistente_e_invalido(client):
    assert client.get("/alunos/68c1230000000000000000aa").status_code == 404
    assert client.get("/alunos/abc").status_code == 404
    assert client.put("/alunos/68c1230000000000000000aa", json=JOAO).status_code == 404
