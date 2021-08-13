from typing import Union

import ocrmypdf
from bson.objectid import ObjectId
from pika.adapters.blocking_connection import BlockingChannel 
from pika.spec import BasicProperties, Basic
from pymongo.database import Database, Collection 
from pytonisacommons import QueueMessage, Queues, log

rabbitmq: Union[dict, None] = None
mongodb_db: Union[Database, None] = None


def on_document_to_process(channel: BlockingChannel, method: Basic.Deliver, properties: BasicProperties, body: Union[str, bytes]):
    collection: Collection = mongodb_db.ocr_request

    ocr_request_id = ObjectId(body.decode())

    log.info('-'*20 + str(ocr_request_id) + '-'*20)
    log.info('Processing document of id ' + str(ocr_request_id))

    document = collection.find_one(
        {'_id': ocr_request_id}
    )
    queue_message = QueueMessage(**document)
    if queue_message.started_processing:
        log.error(
            'Tentando processar um item repetido, provavelmente o servidor crashou no reconhecimento OCR anterior')
        collection.update_one(
            {'_id': ocr_request_id},
            {
                '$set': {
                    'error': True,
                    'errors': ['Tentando processar um item repetido, provavelmente o servidor crashou no reconhecimento OCR anterior']
                }
            }
        )

        channel.basic_publish(
            exchange='',
            routing_key=Queues.ERROR.value,
            body=body,
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
        log.error('Não foi possível processar alguma das línguas solicitadas', mde)
        collection.update_one(
            {'_id': ocr_request_id},
            {
                '$set': {
                    'error': True,
                    'errors': ['Não foi possível processar alguma das línguas solicitadas']
                }
            }
        )

        channel.basic_publish(
            exchange='',
            routing_key=Queues.ERROR.value,
            body=body,
        )

        raise mde
    except Exception as e:
        log.error('Ocorreu um erro desconhecido', e)
        collection.update_one(
            {'_id': ocr_request_id},
            {
                '$set': {
                    'error': True,
                    'errors': ['Ocorreu um erro desconhecido']
                }
            }
        )

        channel.basic_publish(
            exchange='',
            routing_key=Queues.ERROR.value,
            body=body,
        )

        raise e

    collection.update_one(
        {'_id': ocr_request_id},
        {'$set': {'processed': True}}
    )

    log.info('Processamento OCR finalizado com sucesso!')

    channel.basic_publish(
        exchange='',
        routing_key=Queues.PROCESSED.value,
        body=body,
    )

    log.info('Documento processado inserido na fila')

    channel.basic_ack(method.delivery_tag)
