import os

from pika.adapters.blocking_connection import BlockingConnection, BlockingChannel
from pika.connection import URLParameters
from pymongo import MongoClient
from pytonisacommons import Queues, log

import queuehandler
from queuehandler import on_document_to_process

rabbitmq_connection_string = os.getenv('RABBITMQ_CONN_STR')
mongodb_connection_string = os.getenv('MONGODB_CONN_STR')


def start_rabbitmq() -> dict:
    connection = BlockingConnection(URLParameters(rabbitmq_connection_string))
    channel: BlockingChannel = connection.channel()

    for queue in Queues:
        channel.queue_declare(queue.value, durable=True)

    rabbitmq = {
        'connection': connection,
        'channel': channel,
    }

    channel.basic_consume(
        queue=Queues.TO_PROCESS.value,
        on_message_callback=on_document_to_process
    )

    return rabbitmq


def exit_rabbitmq(rabbitmq: dict):
    connection: BlockingConnection = rabbitmq['connection']
    connection.close()


def start_mongodb() -> MongoClient:
    client = MongoClient(mongodb_connection_string)

    mongodb = client
    return mongodb


def exit_mongodb(mongodb: MongoClient):
    pass


def main() -> None:
    rabbitmq, mongodb = start_rabbitmq(), start_mongodb(),

    queuehandler.rabbitmq = rabbitmq
    queuehandler.mongodb_db = mongodb.pytonisa

    log.info('ocrmypdf processor initiated')

    try:
        channel: BlockingChannel = rabbitmq['channel']
        channel.start_consuming()
    except KeyboardInterrupt:
        exit_rabbitmq(rabbitmq), exit_mongodb(mongodb),


if __name__ == '__main__':
    try:
        main()
    except:
        log.exception('Uncaugh exception...')
