import logging as l

from aiogram import Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

rt = Router()

log = l.getLogger(__name__)

class UploadFile(StatesGroup):
    choosing_file = State()
    asking_question = State()


@rt.message(StateFilter(None), Command("upload"))
async def cmd_upload(message: Message, state: FSMContext):
    log.debug("Received /upload command")
    await message.answer("Выберите файл для загрузки. txt или pdf.")
    await state.set_state(UploadFile.choosing_file)