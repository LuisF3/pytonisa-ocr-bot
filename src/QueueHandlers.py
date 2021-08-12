import asyncio

from aio_pika import IncomingMessage

telegram = None
rabbitmq = None

async def on_document_processed(message: IncomingMessage):
    # print(" [x] Received message %r" % message)
    print("Message body is: %r" % message.body)