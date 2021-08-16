from typing import Union, List
from functools import partial
from threading import Thread

import ocrmypdf
from bson.objectid import ObjectId
from pika.adapters.blocking_connection import BlockingConnection, BlockingChannel
from pika.spec import Basic, BasicProperties
from pymongo import message
from pymongo.database import Collection, Database
from pytonisacommons import QueueMessage, Queues, log

rabbitmq: Union[dict, None] = None
mongodb_db: Union[Database, None] = None


def ack_message(delivery_tag, routing_key, message, nack=False):
    """Note that `channel` must be the same pika channel instance via which
    the message being ACKed was retrieved (AMQP protocol constraint).
    """
    channel: BlockingChannel = rabbitmq['channel']
    if channel.is_open:
        channel.basic_publish(
            exchange='',
            routing_key=routing_key,
            body=message,
        )

        if not nack:
            channel.basic_ack(delivery_tag)
        else:
            channel.basic_nack(delivery_tag)
    else:
        # Channel is already closed, so we can't ACK this message;
        # log and/or do something that makes sense for your app in this case.
        pass


def handle_error(channel: BlockingChannel, collection: Collection, ocr_request_id: ObjectId, delivery_tag, message: str, e: Exception=None):
    connection: BlockingConnection = rabbitmq['connection']
    log.error(message, exc_info=e)
    collection.update_one(
        {'_id': ocr_request_id},
        {
            '$set': {
                'error': True,
            },
            '$push': {
                'errors': message,
            }
        }
    )

    cb = partial(ack_message, delivery_tag=delivery_tag, routing_key=Queues.ERROR.value, message=str(ocr_request_id).encode())
    connection.add_callback_threadsafe(cb)


def on_document_to_process(channel: BlockingChannel, method: Basic.Deliver, properties: BasicProperties, body: Union[str, bytes]):
    connection: BlockingConnection = rabbitmq['connection']
    collection: Collection = mongodb_db.ocr_request

    ocr_request_id = ObjectId(body.decode())

    handle_error_partial: function = partial(
        handle_error,
        channel=channel,
        collection=collection,
        ocr_request_id=ocr_request_id,
        delivery_tag=method.delivery_tag
    )

    log.info('-'*20 + str(ocr_request_id) + '-'*20)
    log.info('Processing document of id ' + str(ocr_request_id))

    document = collection.find_one(
        {'_id': ocr_request_id}
    )
    queue_message = QueueMessage(**document)
    
    if queue_message.started_processing:
        handle_error_partial(
            message='Tentando processar um item repetido, provavelmente o servidor crashou no reconhecimento OCR anterior'
        )
        return

    collection.update_one(
        {'_id': ocr_request_id},
        {'$set': {'started_processing': True}}
    )
    queue_message.started_processing = True

    log.info('Iniciando processamento OCR')

    try:
        ocrmypdf.ocr(**queue_message.ocr_args)
    except ocrmypdf.PriorOcrFoundError:
        log.info('Arquivo já possui OCR')
        queue_message.ocr_args['deskew'] = False
        queue_message.ocr_args['clean-final'] = False
        queue_message.ocr_args['remove-background'] = False
        queue_message.ocr_args['redo_ocr'] = True

        collection.update_one(
            {'_id': ocr_request_id},
            {'$set': {'ocr_args': queue_message.ocr_args}}
        )

        ocrmypdf.ocr(**queue_message.ocr_args)
    except ocrmypdf.MissingDependencyError as mde:
        handle_error_partial(
            message='Não foi possível processar alguma das línguas solicitadas',
            e=mde,
        )
        return
    except Exception as e:
        handle_error_partial(
            message='Ocorreu um erro desconhecido',
            e=e,
        )
        return

    collection.update_one(
        {'_id': ocr_request_id},
        {'$set': {'processed': True}}
    )

    log.info('Processamento OCR finalizado com sucesso!')

    cb = partial(ack_message, delivery_tag=method.delivery_tag, routing_key=Queues.PROCESSED.value, message=body)
    connection.add_callback_threadsafe(cb)


def on_document_to_process_thread_handler(channel: BlockingChannel, method: Basic.Deliver, properties: BasicProperties, body: Union[str, bytes], threads: List[Thread]):
    # this is implemented with threads because when the processing takes longer than 60 seconds,
    # rabbitmq closes the connection with error 'missing heartbeats'
    # https://stackoverflow.com/questions/51752890/how-to-disable-heartbeats-with-pika-and-rabbitmq
    t = Thread(target=on_document_to_process, args=(channel, method, properties, body))
    t.start()
    threads.append(t)
