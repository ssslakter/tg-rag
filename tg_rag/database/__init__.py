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


def get_db(embedder, name: str, **kwargs) -> SearchEngine:
    cfg = configs[name](embedding_size=embedder.dim)
    for k, v in kwargs.items():
        setattr(cfg, k, v)
    return engines[name](cfg)
