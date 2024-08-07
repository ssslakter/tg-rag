import asyncio
import logging as l

from aiogram import Bot, Dispatcher, F, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart, CommandObject, StateFilter, and_f, or_f
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from fastcore.all import call_parse

from tg_rag import state_machine as sm
from tg_rag.filters.file_filter import FileFilter
from tg_rag.llm import LLM
from tg_rag.preprocess.data_extraction import download_book, parse_file
from tg_rag.preprocess.text_parsing import parse_book
from tg_rag.utils import init_logger

dp = Dispatcher()
dp.include_router(sm.rt)


log = l.getLogger(__name__.split(".")[0])

question_system_prompt = """
Пользователь задает вопрос о книге.
Напишите список ключевых слов, которые могут помочь найти цитату из книги, отвечающую на вопрос.
Не используйте слова, не связанные с вопросом.
Ответ дайте только списком слов, на русском языке.
"""

answer_system_prompt = """
Пользователь задает вопрос о книге.
Ответьте на вопрос, основываясь на извлеченных абзацах ниже, укажите номера параграфов в виде #1, #2, #4 и т.д., подтверждающих ваш ответ.
Если вопрос нельзя ответить на основе контекста, скажите "Я не знаю".
Внимательно вчитывайся в смысл предложений. Отвечай на русском
"""


@dp.message(or_f(CommandStart(), Command("help")))
async def command_start_handler(message: Message):
    """
    This handler receives messages with `/start` command
    """
    info ='''
    Этот бот позволяет загружать документы и искать в них информацию.
    Список доступных команд:
    /upload - загрузить документ
    /list - список загруженных документов
    /delete <num> - удалить документ по номеру
    /clear - удалить все документы
    /help - отобразить это сообщение
    /default - загрузить книгу по умолчанию (Мастер и Маргарита)
    После загрузки документов можно задать текстом вопрос. Поиск будет производиться по всем загруженным документам.
    '''
    await message.answer(text=info, parse_mode=ParseMode.MARKDOWN)
    

@dp.message(Command("default"))
async def load_default_book(message: Message):
    await message.answer("Загрузка книги по умолчанию...")
    text = download_book(cfg.book_url)
    paragraphs = parse_book(text)
    embs = embedder(paragraphs)
    db.add(str(message.from_user.id), "Master_i_Margarita.txt", embs, paragraphs)
    await message.answer("Книга загружена.")


@dp.message(Command("list"))
async def list_files(message: Message, state: FSMContext):
    files = db.get_all(str(message.from_user.id))
    if not files:
        await message.answer("No files uploaded")
        return
    log.debug(f"Files: {files}")
    await state.update_data(files=list(files))
    await state.set_state(sm.ListState.got_list)
    await message.answer("\n".join([f"{i+1}. {f}" for i, f in enumerate(files)]))
    

@dp.message(sm.ListState.got_list, Command("delete"))
async def delete_file(message: Message, command: CommandObject, state: FSMContext):
    files = (await state.get_data()).get("files")
    if command.args is None:
        await message.answer("Указать номер файла для удаления. /delete <номер>", parse_mode=ParseMode.MARKDOWN)
    try:
        number = int(command.args)
        assert 0 < number <= 10
    except TypeError or AssertionError:
        await message.answer("Некорректный номер файла")
        return
    db.delete(str(message.from_user.id), files[number-1])
    await state.clear()
    await message.answer("Файл удален")


@dp.message(Command("clear"))
async def clear_files(message: Message):
    db.clear(str(message.from_user.id))
    await message.answer("Все файлы удалены.")


@dp.message(sm.UploadFile.choosing_file, FileFilter())
async def load_file(message: Message, state: FSMContext):
    file_id = message.document.file_id
    file = await bot.download(file_id)
    fname = message.document.file_name

    ext = fname.split(".")[-1]
    text = parse_file[ext](file)

    paragraphs = parse_book(text)
    embs = embedder(paragraphs)

    db.add(str(message.from_user.id), fname, embs, paragraphs)
    await state.clear()


@dp.message(sm.UploadFile.choosing_file)
async def load_file_error(message: Message):
    await message.answer("Загрузите файл в формате txt или pdf.")


@dp.message(and_f(~F.text.startswith('/'), ~FileFilter()))
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
    docs, scores = db.search(str(message.from_user.id), emb, query, cfg.max_docs)

    log.info(f"Found {len(docs)} relevant paragraphs")
    log.debug(f"Scores are: {scores}")

    concat_docs = "\n\n".join([f"### {i+1}\n\n{s}" for i, s in enumerate(docs)])
    log.debug(f"Found docs:\n{concat_docs}")
    ans = llm.prompt(message.text, answer_system_prompt + concat_docs)
    log.debug(f"Answer is: {ans}")
    try:
        res = await message.reply(ans)
        import re
        regex = re.compile(r"#(\d+)")
        numbers = [int(i) for i in regex.findall(ans)]
        quotes = [f'### {i}' + '\n' + docs[i-1] for i in numbers]
        await res.reply("Цитаты\n\n".join(quotes))
    except TypeError:
        await message.answer("Unexpected error occurred. Please try again later.")


async def async_main(db_name: str, only_text: bool, embedding_model: str,
                     api_url: str, model: str, v: bool):
    from tg_rag.config import Config
    from tg_rag.database import get_db
    from tg_rag.embedding import Embedder

    init_logger(log.name, level=l.DEBUG if v else l.INFO)
    global llm, cfg, db, embedder, bot
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
    bot = Bot(token=cfg.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    await bot.delete_webhook(drop_pending_updates=True)
    log.info("Starting the bot...")
    await dp.start_polling(bot)


@call_parse
def main(db_name: str = "qdrant",  # "Database to use: elastic or qdrant"
         only_text: bool = False,  # "If True, only using full-text search"
         embedding_model: str = "cointegrated/rubert-tiny2",  # "Sentence transformer model to use. Unused if `only_text` is True"
         api_url: str = "http://localhost:11434",  # "URL of the LLM API"
         model: str = "llama3",  # "Model to use for LLM"
         v: bool = False  # "Verbose mode"
         ):
    asyncio.run(async_main(db_name, only_text, embedding_model, api_url, model, v))


if __name__ == "__main__":
    main()
