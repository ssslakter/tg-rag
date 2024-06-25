import logging as l
from dataclasses import dataclass
from uuid import uuid4

from fastprogress import progress_bar
from qdrant_client import QdrantClient, models

from tg_rag.database.basic import SearchEngine

log = l.getLogger(__name__)


@dataclass
class QdrantConfig:
    url: str = "http://localhost:6333"
    collection_name: str = "my_collection"
    embedding_size: int = 768
    override: bool = False
    bs: int = 64


class QdrantEngine(SearchEngine):
    def __init__(self, client_cfg: QdrantConfig):
        self.client = QdrantClient(url=client_cfg.url)
        self.cfg = client_cfg
        if not self.client.collection_exists(self.cfg.collection_name) or self.cfg.override:
            log.info(f"Creating collection {self.cfg.collection_name}")
            self.client.recreate_collection(self.cfg.collection_name,
                                            vectors_config=models.VectorParams(
                                                size=self.cfg.embedding_size,
                                                distance=models.Distance.COSINE
                                            ))

    def search(self, query, max_docs: int = 50):
        hits = self.client.search(self.cfg.collection_name, query, limit=max_docs)
        return zip(*((hit.payload["text"], hit.score) for hit in hits))

    def add(self, embeddings: list, documents: list):
        for i in progress_bar(range(0, len(documents), self.cfg.bs)):
            ri = min(i + self.cfg.bs, len(documents))
            self._add_batch(embeddings[i:ri], documents[i:ri])

    def _add_batch(self, embeddings, documents):
        return self.client.upsert(self.cfg.collection_name, points=[
            models.PointStruct(id=str(uuid4()), vector=emb, payload={"text": doc})
            for emb, doc in zip(embeddings, documents)
        ], wait=True)
