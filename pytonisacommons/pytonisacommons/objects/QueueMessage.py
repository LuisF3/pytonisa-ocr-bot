from __future__ import annotations
from .PytonisaDB import DatabaseEntry
from .OcrArgs import OcrArgs

class QueueMessage(DatabaseEntry):
    __ocr_args_subclasses__: dict
    def __init__(
        self,
        chat_id: int,
        message_id: int,
        ocr_args: OcrArgs | dict,
        file_name: str,
        _id: str=None,
        started_processing: bool=False,
        processed: bool=False,
        error: bool=False,
        errors: bool=None,
    ) -> None:
        super().__init__(_id)
        self.chat_id: int = int(chat_id)
        self.message_id: int = int(message_id)
        self.ocr_args: OcrArgs = ocr_args
        self.file_name: str = file_name
        self.started_processing: bool = started_processing
        self.processed: bool = processed
        self.error: bool = error
        self.errors: list[str] = errors if errors is not None else []
