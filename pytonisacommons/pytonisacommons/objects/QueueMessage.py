from __future__ import annotations
from .PytonisaDB import DatabaseEntry
from .OcrArgs import OcrArgs

class QueueMessage(DatabaseEntry):
    def __init__(
        self,
        file_name: str,
        chat_id: int,
        message_id: int,
        ocr_args: OcrArgs | dict,
        _id: str=None,
        started_processing: bool=False,
        processed: bool=False,
        error: bool=False,
        errors: bool=None,
    ) -> None:
        super().__init__(_id)
        self.file_name: str = file_name
        self.chat_id: int = int(chat_id)
        self.message_id: int = int(message_id)
        self.ocr_args: OcrArgs = ocr_args
        self.started_processing: bool = started_processing
        self.processed: bool = processed
        self.error: bool = error
        self.errors: list[str] = errors if errors is not None else []

    def get_args(self) -> dict:
        return self.ocr_args.get_args()

    def to_dict(self) -> dict:
        queue_m = self.__dict__.copy()
        if not type(self.ocr_args) is dict:
            queue_m['ocr_args'] = self.ocr_args.__dict__.copy()