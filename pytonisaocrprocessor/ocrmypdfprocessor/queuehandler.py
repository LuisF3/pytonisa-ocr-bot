from aio_pika import IncomingMessage
from pytonisacommons import log
from pytonisacommons import Queues
from typing import Union
from motor.core import Database, Collection
from bson.objectid import ObjectId
from pytonisacommons import QueueMessage
import ocrmypdf
from aio_pika import Channel, Message

rabbitmq: Union[dict, None] = None
mongodb_db: Union[Database, None] = None

async def on_document_to_process(message: IncomingMessage):
    collection: Collection = mongodb_db.ocr_request
    channel: Channel = rabbitmq['channel']

    ocr_request_id = ObjectId(message.body.decode())

    log.info('Processing document of id ' + str(ocr_request_id))

    document = await collection.find_one(
        {'_id': ocr_request_id}
    )
    queue_message = QueueMessage(**document)

    if queue_message.started_processing:
        log.error('Tentando processar um item repetido, provavelmente o servidor crashou no reconhecimento OCR anterior')
        await collection.update_one(
            {'_id': ocr_request_id},
            {
                '$set': {
                    'error': True,
                    'errors': [ 'Tentando processar um item repetido, provavelmente o servidor crashou no reconhecimento OCR anterior' ]
                }
            }
        )

        await channel.default_exchange.publish(Message(message.body), routing_key=Queues.ERROR.value)

        raise Exception('Tentando processar um item com started_processing=True. Provavelmente o sistema crashou em um processamento anterior')

    await collection.update_one(
        {'_id': ocr_request_id},
        {'$set': {'started_processing': True }}
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

        await collection.update_one(
            {'_id': ocr_request_id},
            {'$set': {'ocr_args': queue_message.ocr_args }}
        )

        ocrmypdf.ocr(**queue_message.ocr_args)
    except ocrmypdf.MissingDependencyError as mde:
        log.error('Não foi possível processar alguma das línguas solicitadas', mde)
        await collection.update_one(
            {'_id': ocr_request_id},
            {
                '$set': {
                    'error': True,
                    'errors': [ 'Não foi possível processar alguma das línguas solicitadas' ]
                }
            }
        )

        await channel.default_exchange.publish(Message(message.body), routing_key=Queues.ERROR.value)

        raise mde
    except Exception as e:
        log.error('Ocorreu um erro desconhecido', e)
        await collection.update_one(
            {'_id': ocr_request_id},
            {
                '$set': {
                    'error': True,
                    'errors': [ 'Ocorreu um erro desconhecido' ]
                }
            }
        )

        await channel.default_exchange.publish(Message(message.body), routing_key=Queues.ERROR.value)
        raise e

    await collection.update_one(
        {'_id': ocr_request_id},
        {'$set': {'processed': True }}
    )

    log.info('Processamento OCR finalizado com sucesso!')

    await channel.default_exchange.publish(Message(message.body), routing_key=Queues.PROCESSED.value)

    log.info('Documento processado inserido na fila')