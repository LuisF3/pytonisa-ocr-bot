import os
from functools import partial
from typing import List
from threading import Thread

from pika.adapters.blocking_connection import (BlockingChannel,
                                               BlockingConnection)
from pika.connection import URLParameters
from pytonisacommons import Queues, log, PytonisaDB, PytonisaFileStorage, PytonisaS3Storage

import queuehandler
from queuehandler import on_document_to_process_thread_handler

rabbitmq_connection_string = os.getenv('RABBITMQ_CONN_STR')

if rabbitmq_connection_string is None:
    raise Exception('RABBITMQ_CONN_STR must be not None')

threads: List[Thread] = []


def start_rabbitmq() -> dict:
    connection = BlockingConnection(URLParameters(rabbitmq_connection_string))
    channel: BlockingChannel = connection.channel()
    channel.basic_qos(prefetch_count=1)

    for queue in Queues:
        channel.queue_declare(queue.value, durable=True)

    rabbitmq = {
        'connection': connection,
        'channel': channel,
    }

    on_document_to_process_thread_handler_partial = partial(on_document_to_process_thread_handler, threads=threads)
    channel.basic_consume(
        queue=Queues.TO_PROCESS.value,
        on_message_callback=on_document_to_process_thread_handler_partial
    )

    return rabbitmq


def exit_rabbitmq(rabbitmq: dict):
    connection: BlockingConnection = rabbitmq['connection']
    channel: BlockingChannel = rabbitmq['channel']
    channel.stop_consuming()
    connection.close()


def start_pytonisadb() -> PytonisaDB:
    return PytonisaDB()

def exit_pytonisadb(pytonisadb: PytonisaDB):
    pytonisadb.close()


def start_pytonisa_file_storage() -> PytonisaFileStorage:
    return PytonisaS3Storage()

def exit_pytonisa_file_storage(pytonisa_files: PytonisaFileStorage) -> PytonisaFileStorage:
    pytonisa_files.close()


def main() -> None:
    rabbitmq, pytonisadb, pytonisa_files = start_rabbitmq(), start_pytonisadb(), start_pytonisa_file_storage()

    queuehandler.rabbitmq = rabbitmq
    queuehandler.pytonisadb = pytonisadb
    queuehandler.pytonisa_files = pytonisa_files

    log.info('ocrmypdf processor initiated')

    try:
        channel: BlockingChannel = rabbitmq['channel']
        channel.start_consuming()
    except KeyboardInterrupt:
        log.info('ending ocrmypdf')
        exit_rabbitmq(rabbitmq), exit_pytonisadb(pytonisadb), exit_pytonisa_file_storage(pytonisa_files)

        for thread in threads:
            thread.join()
        log.info('ocrmypdf ended')



if __name__ == '__main__':
    try:
        main()
    except:
        log.exception('Uncaugh exception...')
