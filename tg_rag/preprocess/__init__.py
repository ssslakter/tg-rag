import logging as l

from fastcore.all import call_parse

from .data_extraction import download_book
from .text_parsing import parse_book


@call_parse
def main(db:str="qdrant",  # "Database to use: elastic or qdrant"
         embedding_model: str ="cointegrated/rubert-tiny2",  # "Sentence transformer model to use"
         max_words: int = 50,  # "Maximum number of words in a paragraph"
         min_words: int = 20,  # "Minimum number of words in a paragraph"
         ):
    from ..config import Config
    from ..embedding import Embedder
    from ..utils import init_logger
    from ..database import get_db
    
    log = l.getLogger(__name__)
    cfg = Config(embedding_model=embedding_model)
    init_logger(log.name)
    
    log.info(f"Using {embedding_model} for embeddings")
    embed = Embedder(embedding_model)
    
    log.info(f"Connecting to {db}")
    client = get_db(embed, db)
    
    log.info(f"Downloading book from {cfg.book_url}")
    book = download_book(cfg.book_url)
    paragraphs = parse_book(book, max_words, min_words)
    
    log.info(f"Extracting embeddings for {len(paragraphs)} paragraphs")
    embeddings = embed(paragraphs)
    
    log.info(f"Adding {len(embeddings)} paragraphs to the database")
    client.add(embeddings, paragraphs)

if __name__ == "__main__":
    main()
