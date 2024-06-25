import asyncio
import logging as l
from fastcore.all import call_parse

from aiogram import Bot, Dispatcher, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message

from tg_rag.database import get_db
from tg_rag.embedding import Embedder

from .config import Config
from .llm import LLM
from .utils import init_logger


dp = Dispatcher()

log = l.getLogger(__name__)

question_system_prompt = """
Пользователь задает вопрос о книге.
Напишите список ключевых слов, которые могут помочь найти цитату из книги, отвечающую на вопрос.
Не используйте слова, не связанные с вопросом.
Ответ дайте только списком слов, на русском языке.
"""

answer_system_prompt = """
Ответьте на вопрос, основываясь на извлеченных абзацах ниже, укажите номер(а) параграфа(ов), подтверждающих ваш ответ.
Если вопрос нельзя ответить на основе контекста, скажите "Я не знаю".
Ответ давайте только на русском языке.
"""


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    """
    This handler receives messages with `/start` command
    """
    await message.answer(f"Hello, {html.bold(message.from_user.full_name)}!")


@dp.message()
async def rag_handler(message: Message) -> None:

    log.info(f"Received message: {message.text}")

    query = llm.prompt(message.text, question_system_prompt
                       ) if cfg.ask_llm_query else message.text
    
    log.info(f"Query for db is: {query}")
    docs, scores = db.search(query, cfg.max_docs)

    log.info(f"Found {len(docs)} relevant paragraphs")
    log.debug(f"Scores are: {scores}")

    concat_docs = "\n\n".join([f"### {i+1}\n\n{s}" for i, s in enumerate(docs)])
    log.debug(f"Found docs:\n{concat_docs}")
    ans = llm.prompt(message.text, message.text + answer_system_prompt + concat_docs)
    try:
        await message.reply(ans.choices[0].message.content)
    except TypeError:
        await message.answer("Unexpected error occurred. Please try again later.")


@call_parse
def main(db_name: str = "qdrant",  # "Database to use: elastic or qdrant"
         embedding_model: str = "cointegrated/rubert-tiny2",  # "Sentence transformer model to use"
         api_url: str = "http://localhost:11434",  # "URL of the LLM API"
         ):
    init_logger("tg_rag", level=l.DEBUG)
    global llm, cfg, db
    cfg = Config(embedding_model=embedding_model, api_url=api_url)
    
    log.info(f"Using {cfg.embedding_model} for embeddings")
    embed = Embedder(cfg.embedding_model)
    
    log.info(f"Connecting to {db_name}")
    db = get_db(embed, db_name)
    
    log.info(f"Connecting to LLM on {cfg.api_url}")
    llm = LLM(cfg)
    log.info("Starting the bot...")
    bot = Bot(token=cfg.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    asyncio.run(dp.start_polling(bot))


if __name__ == "__main__":
    main()
