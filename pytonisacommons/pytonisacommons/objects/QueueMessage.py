class QueueMessage:
    def __init__(self, chat_id: int, message_id: int, ocr_args: dict, _id=None, *args, **kwargs) -> None:
        if _id:
            self._id = _id
        self.chat_id: int = chat_id
        self.message_id: int = message_id
        self.ocr_args: dict = ocr_args
        self.started_processing: bool = False
        self.error: bool = False
        self.errors: list[str] = []
