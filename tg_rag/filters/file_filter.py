import logging as l
from typing import Union

from aiogram.filters import BaseFilter
from aiogram.types import Message

log = l.getLogger(__name__)

class FileFilter(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        file = message.document
        if file is None:
            log.debug("No file in message")
            return False
        log.debug(f"Checking file {file.file_name}")
        return file.mime_type in ("application/pdf", "text/plain")