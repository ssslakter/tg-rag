import asyncio
import logging as l

from aiogram import Bot, Dispatcher, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message

from fastcore.all import call_parse

from tg_rag.llm import LLM
from tg_rag.utils import init_logger

dp = Dispatcher()

log = l.getLogger(__name__.split(".")[0])

question_system_prompt = """
Пользователь задает вопрос о книге.
Напишите список ключевых слов, которые могут помочь найти цитату из книги, отвечающую на вопрос.
Не используйте слова, не связанные с вопросом.
Ответ дайте только списком слов, на русском языке.
"""

answer_system_prompt = """
Ответьте на вопрос, основываясь на извлеченных абзацах ниже, укажите номер(а) параграфа(ов) и их текст, подтверждающих ваш ответ.
Если вопрос нельзя ответить на основе контекста, скажите "Я не знаю".
Внимательно вчитывайся в смысл предложений. Отвечай на русском
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
    if len(message.text) < 5 or len(message.text) > 500:
        await message.answer("Сообщение не подходит по размерам. Пожалуйста, уточните вопрос. (ANTI-SPAM)")
        return
    query = llm.prompt(message.text, question_system_prompt
                       ) if cfg.ask_llm_query else message.text
    
    log.info(f"Query for db is: {query}")

    embedder = globals().get("embedder", None)
    if embedder is not None: emb = embedder(query)[0]
    else: emb = None
    docs, scores = db.search(emb, query, cfg.max_docs)

    log.info(f"Found {len(docs)} relevant paragraphs")
    log.debug(f"Scores are: {scores}")

    concat_docs = "\n\n".join([f"### {i+1}\n\n{s}" for i, s in enumerate(docs)])
    log.debug(f"Found docs:\n{concat_docs}")
    ans = llm.prompt(message.text, message.text + answer_system_prompt + concat_docs)
    log.debug(f"Answer is: {ans}")
    try:
        await message.reply(ans)
    except TypeError:
        await message.answer("Unexpected error occurred. Please try again later.")


@call_parse
def main(db_name: str = "qdrant",  # "Database to use: elastic or qdrant"
         only_text: bool = False,  # "If True, only using full-text search"
         embedding_model: str = "cointegrated/rubert-tiny2",  # "Sentence transformer model to use. Unused if `only_text` is True"
         api_url: str = "http://localhost:11434",  # "URL of the LLM API"
         model: str = "llama3",  # "Model to use for LLM"
         v: bool = False  # "Verbose mode"
         ):
    from tg_rag.config import Config
    from tg_rag.database import get_db
    from tg_rag.embedding import Embedder
    
    init_logger(log.name, level=l.DEBUG if v else l.INFO)
    global llm, cfg, db, embedder
    cfg = Config(embedding_model=embedding_model, api_url=api_url, model=model)
    
    if not only_text: 
        log.info(f"Using {cfg.embedding_model} for embeddings")
        embedder = Embedder(cfg.embedding_model)
        dim = embedder.dim
    else: dim = 1
    
    log.info(f"Connecting to {db_name}")
    db = get_db(dim, db_name, override=False)
    
    log.info(f"Connecting to LLM on {cfg.api_url}")
    llm = LLM(cfg)
    log.info("Starting the bot...")
    bot = Bot(token=cfg.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    asyncio.run(dp.start_polling(bot))


if __name__ == "__main__":
    main()
