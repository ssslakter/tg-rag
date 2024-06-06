from dataclasses import dataclass
from os import getenv

@dataclass
class Config:
    book_url: str = "https://github.com/MenshikovDmitry/TSU_AI_Course/raw/main/module_4.%20RAG/Bulgakov_Mihail_Master_i_Margarita_Readli.Net_bid256_5c1f5.txt.zip"
    es_url: str = "http://localhost:9200"
    es_creds: tuple = ("elastic", "elastic")
    api_token: str = getenv("HF_TOKEN", None)
    api_url: str = "https://api-inference.huggingface.co/models/TheBloke/Llama-2-7B-GGML"
    bot_token: str = getenv("BOT_TOKEN", None)
