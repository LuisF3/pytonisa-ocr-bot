import asyncio
import os

from aio_pika import Channel, Connection, Queue, connect_robust
from pymongo import MongoClient
from pytonisacommons import Queues, log

import queuehandler
from queuehandler import on_document_to_process

rabbitmq_connection_string = os.getenv('RABBITMQ_CONN_STR')
mongodb_connection_string = os.getenv('MONGODB_CONN_STR')


async def start_rabbitmq(loop: asyncio.AbstractEventLoop) -> dict:
    connection = await connect_robust(rabbitmq_connection_string, loop=loop)
    channel: Channel = await connection.channel()

    queues: dict[str, Queue] = {}
    for queue in Queues:
        queues[queue.value] = await channel.declare_queue(queue.value, durable=True)

    rabbitmq = {
        'connection': connection,
        'channel': channel,
        'queues': queues
    }

    loop.create_task(
        queues[Queues.TO_PROCESS.value].consume(
            on_document_to_process, no_ack=True)
    )

    return rabbitmq


async def exit_rabbitmq(rabbitmq: dict):
    connection: Connection = rabbitmq['connection']
    await connection.close()


async def start_mongodb() -> MongoClient:
    client = MongoClient(mongodb_connection_string)

    mongodb = client
    return mongodb


async def exit_mongodb(mongodb: MongoClient):
    pass


def main(loop: asyncio.AbstractEventLoop) -> None:
    rabbitmq, mongodb = loop.run_until_complete(
        asyncio.gather(
            start_rabbitmq(loop),
            start_mongodb(),
        )
    )

    queuehandler.rabbitmq = rabbitmq
    queuehandler.mongodb_db = mongodb.pytonisa

    log.info('ocrmypdf processor initiated')

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        loop.run_until_complete(
            asyncio.gather(
                exit_rabbitmq(rabbitmq),
                exit_mongodb(mongodb),
            )
        )


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    try:
        main(loop)
    except:
        log.exception('Uncaugh exception...')
