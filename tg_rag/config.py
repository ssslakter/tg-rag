from dataclasses import dataclass
from os import getenv


@dataclass
class Config:
    book_url: str = "https://github.com/MenshikovDmitry/TSU_AI_Course/raw/main/module_4.%20RAG/Bulgakov_Mihail_Master_i_Margarita_Readli.Net_bid256_5c1f5.txt.zip"
    api_token: str = getenv("API_KEY", 'no_token')
    api_url: str = "http://localhost:11434"
    model: str = "llama3"
    bot_token: str = getenv("BOT_TOKEN", None)
    ask_llm_query: bool = False
    max_docs: int = 8
    embedding_model: str = "cointegrated/rubert-tiny2"
    only_text: bool = False
