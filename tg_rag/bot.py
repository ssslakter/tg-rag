import os
import asyncio
import logging as l
from email import message

from aiogram import Bot, Dispatcher, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message

from tg_rag.llm import LLM
from tg_rag.search import Search
from tg_rag.utils import init_logger

from tg_rag.config import Config  
cfg = Config()
cfg.api_token = "a"
cfg.bot_token = "7050156356:AAH_9sWYFU3AwsTn65u93xSQIWZcj4dZ0WE"
dp = Dispatcher()
llm = LLM(cfg)
search = Search(cfg)
question_prompt = """
Вы являетесь экспертом в области русского языка и литературы.
Вы с лёгкостью можете отвечать на вопросы о различных романах и стихотворениях."""

user_preface = """
Ваша задача — создать запрос для TF-IDF поиска релевантных абзацев в книге Мастер и Маргарита, которые помогут ответить на вопрос.
Создай *один* короткий запрос на русском, по которому будет производиться поиск.
"""

answer_prompt = """
Имея абзацы из книги Мастер и Маргарита, ответьте на поставленный вопрос. Приведи цитаты из предоставленных абзацев. Отвечай на русском:
"""


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    """
    This handler receives messages with `/start` command
    """
    await message.answer(f"Hello, {html.bold(message.from_user.full_name)}!")


@dp.message()
async def rag_handler(message: Message) -> None:
    
    l.info(f"Received message: {message.text}")
    
    res = llm.prompt(message.text, question_prompt)
    query = res.choices[0].message.content
    l.info(f"Received response: {query}")
    docs = search.search(query)
    l.info(f"Found {len(docs)} relevant paragraphs")
    concat_docs = '\n'.join(docs)
    concat_docs = concat_docs[:min(4096, len(concat_docs))]
    ans = llm.prompt(message.text, message.text+answer_prompt+concat_docs)
    try:
        # Send a copy of the received message
        await message.reply(ans.choices[0].message.content)
    except TypeError:
        # But not all the types is supported to be copied so need to handle it
        await message.answer("Nice try!")


def main():
    init_logger()
    l.info("Starting the bot...")
    bot = Bot(token=cfg.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    asyncio.run(dp.start_polling(bot))


if __name__ == "__main__":
    message = user_preface+"Кто такой мастер?"
    res = llm.prompt(message, question_prompt)
    query = res.choices[0].message.content
    l.info(f"Received response: {res.choices[0].message.content}")
    docs = search.search(res.choices[0].message.content)
    l.info(f"Found {len(docs)} relevant paragraphs")
    l.debug(docs)
    
    main()
