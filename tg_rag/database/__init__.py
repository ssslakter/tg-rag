from .basic import SearchEngine
from .elastic import ElasticConfig, ElasticEngine
from .qdrant import QdrantConfig, QdrantEngine

engines = {
    "elastic": ElasticEngine,
    "qdrant": QdrantEngine
}

configs = {
    "elastic": ElasticConfig,
    "qdrant": QdrantConfig
}


def get_db(embedder, name: str, cfg=None) -> SearchEngine:
    if not cfg: cfg = configs[name](embedding_size=embedder.dim)
    return engines[name](cfg)
