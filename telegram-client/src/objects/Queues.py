from enum import Enum

class Queues(Enum):
    TO_PROCESS = 'to_process'
    PROCESSED = 'successfully_processed'
    ERROR = 'error'