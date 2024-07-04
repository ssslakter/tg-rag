import logging as l

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

log = l.getLogger(__name__)

def get_db(embed_dim, name: str, **kwargs) -> SearchEngine:
    cfg = configs[name](embedding_size=embed_dim)
    log.debug(f"Creating {name} engine with config: {cfg}")
    for k, v in kwargs.items():
        setattr(cfg, k, v)
    return engines[name](cfg)
