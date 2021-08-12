class QueueMessage:
    def __init__(self, chat_id, message_id, args) -> None:
        self.chat_id = chat_id
        self.message_id = message_id
        self.args = args
        self.started_processing = False
        self.error = False