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
    override: bool = True
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

    def search(self, nickname, embedding, query, max_docs: int = 50):
        hits = self.client.search(self.cfg.collection_name, embedding,
                                  query_filter=models.Filter(
                                      must=[models.FieldCondition(
                                          key="nickname",
                                          match=models.MatchValue(value=nickname))]),
                                  limit=max_docs
                                  )
        return zip(*((hit.payload["text"], hit.score) for hit in hits))

    def add(self, nickname: str, filename: str, embeddings: list, documents: list):
        for i in progress_bar(range(0, len(documents), self.cfg.bs)):
            ri = min(i + self.cfg.bs, len(documents))
            self._add_batch(nickname, filename, embeddings[i:ri], documents[i:ri])

    def _add_batch(self, nickname, filename, embeddings, documents):
        return self.client.upsert(self.cfg.collection_name, points=[
            models.PointStruct(id=str(uuid4()), vector=emb, payload={
                               "filename": filename, "text": doc, "nickname": nickname})
            for emb, doc in zip(embeddings, documents)
        ], wait=True)

    def clear(self, nickname: str):
        self.client.delete(self.cfg.collection_name, points_selector=models.FilterSelector(
            filter=models.Filter(
                must=[models.FieldCondition(key="nickname", match=models.MatchValue(value=nickname))])
        ))

    def get_all(self, nickname: str):
        result, _ = self.client.scroll(self.cfg.collection_name,
                                       scroll_filter=models.Filter(
                                           must=[models.FieldCondition(
                                               key="nickname",
                                               match=models.MatchValue(value=nickname))]
                                       ), limit=1000, with_vectors=False, with_payload=True)
        fnames = set(hit.payload["filename"] for hit in result)
        return fnames
