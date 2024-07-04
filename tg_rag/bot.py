import asyncio
import logging as l

from aiogram import Bot, Dispatcher, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message
from click import Command
from fastcore.all import call_parse

from tg_rag.llm import LLM
from tg_rag.preprocess.text_parsing import parse_book
from tg_rag.utils import init_logger
from tg_rag.preprocess.data_extraction import parse_file

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
Внимательно вчитывайся в смысл предложений. Отвечай на русском
"""


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    """
    This handler receives messages with `/start` command
    """
    await message.answer(f"Hello, {html.bold(message.from_user.full_name)}! Add your documents to the database.")

@dp.message()
async def rag_handler(message: Message) -> None:

    log.info(f"Received message: {message.text}")

    query = llm.prompt(message.text, question_system_prompt
                       ) if cfg.ask_llm_query else message.text
    
    log.info(f"Query for db is: {query}")
    emb = embedder(query)[0]
    docs, scores = db.search(emb, query, cfg.max_docs)

    log.info(f"Found {len(docs)} relevant paragraphs")
    log.debug(f"Scores are: {scores}")

    concat_docs = "\n\n".join([f"### {i+1}\n\n{s}" for i, s in enumerate(docs)])
    log.debug(f"Found docs:\n{concat_docs}")
    ans = llm.prompt(message.text, message.text + answer_system_prompt + concat_docs)
    try:
        await message.reply(ans)
    except TypeError:
        await message.answer("Unexpected error occurred. Please try again later.")


@dp.message(Command("upload"))
async def load_file(message: Message):
    file_id = message.document.file_id
    file = await bot.download(file_id)
    fname = message.document.file_name
    
    ext = fname.split(".")[-1]
    text = parse_file[ext](file)
    
    paragraphs = parse_book(text)
    embs = embedder(paragraphs)
    
    db.add(embs, paragraphs, str(message.from_user.id))


@dp.message(Command("clear"))
async def clear_files(message: Message):
    db.clear(str(message.from_user.id))


@call_parse
def main(db_name: str = "qdrant",  # "Database to use: elastic or qdrant"
         embedding_model: str = "cointegrated/rubert-tiny2",  # "Sentence transformer model to use"
         api_url: str = "http://localhost:11434",  # "URL of the LLM API"
         model: str = "llama3",  # "Model to use for LLM"
         ):
    from tg_rag.config import Config
    from tg_rag.database import get_db
    from tg_rag.embedding import Embedder
    
    init_logger("tg_rag", level=l.DEBUG)
    global llm, cfg, db, embedder, bot
    cfg = Config(embedding_model=embedding_model, api_url=api_url, model=model)
    
    log.info(f"Using {cfg.embedding_model} for embeddings")
    embedder = Embedder(cfg.embedding_model)
    
    log.info(f"Connecting to {db_name}")
    db = get_db(embedder, db_name, override=False)
    
    log.info(f"Connecting to LLM on {cfg.api_url}")
    llm = LLM(cfg)
    log.info("Starting the bot...")
    bot = Bot(token=cfg.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    asyncio.run(dp.start_polling(bot))


if __name__ == "__main__":
    main()
