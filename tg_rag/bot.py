import asyncio
import logging as l

from aiogram import Bot, Dispatcher, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message

from .config import Config
from .llm import LLM
from .search import vector
from .search.text import Search
from .utils import init_logger

cfg = Config()
dp = Dispatcher()
llm = LLM(cfg)
search = Search(cfg)
# search = vector.Search("vec_index", cfg)

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
    
    if cfg.ask_llm_query:
        res = llm.prompt(message.text, question_system_prompt)
        query = res.choices[0].message.content
    else: query = message.text
    
    log.info(f"Query for elastic is: {query}")
    # docs, scores = search.search(query, cfg.max_docs)
    docs, scores = search.knn_search(query)
    
    log.info(f"Found {len(docs)} relevant paragraphs")
    log.debug(f"Scores are: {scores}")
    
    concat_docs = "\n\n".join([f"### {i+1}\n\n{s}" for i, s in enumerate(docs)])
    log.debug(f"Found docs:\n{concat_docs}")
    ans = llm.prompt(message.text, message.text+answer_system_prompt+concat_docs)
    try:
        await message.reply(ans.choices[0].message.content)
    except TypeError:
        await message.answer("Unexpected error occurred. Please try again later.")


def main():
    init_logger("tg_rag", level=l.DEBUG)
    log.info("Starting the bot...")
    bot = Bot(token=cfg.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    asyncio.run(dp.start_polling(bot))


if __name__ == "__main__":
    main()
