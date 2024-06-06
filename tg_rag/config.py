

from dataclasses import dataclass


@dataclass
class Config:
    book_url: str = "https://github.com/MenshikovDmitry/TSU_AI_Course/raw/main/module_4.%20RAG/Bulgakov_Mihail_Master_i_Margarita_Readli.Net_bid256_5c1f5.txt.zip"
    es_url: str = "http://localhost:9200"
    es_creds: tuple = ("elastic", "elastic")