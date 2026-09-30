"""Conexão com o MongoDB (banco: escola / coleção: alunos)."""
import os

from pymongo import ASCENDING, MongoClient
from pymongo.collection import Collection

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("MONGO_DB", "escola")
COLLECTION_NAME = "alunos"

_client: MongoClient | None = None


def get_client() -> MongoClient:
    global _client
    if _client is None:
        _client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    return _client


def get_collection() -> Collection:
    return get_client()[DB_NAME][COLLECTION_NAME]


def init_db() -> None:
    """Cria índice único em e-mail (garante a regra de e-mail duplicado no próprio banco)."""
    get_collection().create_index([("email", ASCENDING)], unique=True, name="uk_email")
