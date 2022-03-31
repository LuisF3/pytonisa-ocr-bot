from typing import Union, List
from functools import partial
from threading import Thread
import os

import ocrmypdf
from pika.adapters.blocking_connection import BlockingConnection, BlockingChannel
from pika.spec import Basic, BasicProperties
from pytonisacommons import QueueMessage, Queues, log, PytonisaDB, DatabaseEntry, OcrMyPdfArgs, PytonisaFileStorage, PytonisaLocalFileStorage

rabbitmq: Union[dict, None] = None
pytonisadb: PytonisaDB = None
pytonisa_files: PytonisaFileStorage = None

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


def handle_error(channel: BlockingChannel, ocr_request_id: str, delivery_tag, message: str, e: Exception = None):
    connection: BlockingConnection = rabbitmq['connection']
    log.error(message, exc_info=e)

    document: dict = pytonisadb.ocr_requests.get_item(ocr_request_id)
    existing_errors: list = document['errors']

    ocr_request_id = pytonisadb.ocr_requests.update_item(ocr_request_id, {
        'error': True,
        'errors': existing_errors + [message],
    })

    cb = partial(ack_message, delivery_tag=delivery_tag,
                 routing_key=Queues.ERROR.value, message=ocr_request_id.encode())
    connection.add_callback_threadsafe(cb)


def on_document_to_process(channel: BlockingChannel, method: Basic.Deliver, properties: BasicProperties, body: Union[str, bytes]):
    connection: BlockingConnection = rabbitmq['connection']
    
    ocr_request_id = body.decode()
    
    handle_error_partial: function = partial(
        handle_error,
        channel=channel,
        ocr_request_id=ocr_request_id,
        delivery_tag=method.delivery_tag
    )

    log.info('-'*20 + ocr_request_id + '-'*20)
    log.info('Processing document of id ' + ocr_request_id)

    document: dict = pytonisadb.ocr_requests.get_item(ocr_request_id)
    queue_message: QueueMessage = QueueMessage(**document)
    queue_message.ocr_args = OcrMyPdfArgs(**queue_message.ocr_args)

    if queue_message.started_processing:
        handle_error_partial(
            message='Tentando processar um item repetido, provavelmente o servidor crashou no reconhecimento OCR anterior'
        )
        return

    queue_message.started_processing = True 
    pytonisadb.ocr_requests.update_item(ocr_request_id, {'started_processing': True})

    queue_message.ocr_args.input_file = pytonisa_files.download_file(queue_message.ocr_args.input_id)
    queue_message.ocr_args.output_file = os.path.join(pytonisa_files.get_valid_path(), queue_message.file_name)

    log.info('Iniciando processamento OCR')

    try:
        ocr_args = queue_message.ocr_args.__dict__
        del ocr_args['input_id']
        ocrmypdf.ocr(**ocr_args)
    except ocrmypdf.PriorOcrFoundError:
        log.info('Arquivo já possui OCR')

        queue_message.ocr_args.set_force_ocr()
        pytonisadb.ocr_requests.update_item(
            ocr_request_id, {'ocr_args': queue_message.ocr_args.__dict__})

        ocr_args = queue_message.ocr_args.__dict__
        del ocr_args['input_id']
        ocrmypdf.ocr(**ocr_args)
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

    queue_message.ocr_args.output_id = pytonisa_files.upload_file(queue_message.ocr_args.output_file)

    queue_message.processed = True
    ocr_args = queue_message.ocr_args.__dict__
    del ocr_args['input_file'], ocr_args['output_file']
    pytonisadb.ocr_requests.update_item(ocr_request_id, {'processed': True, 'ocr_args': ocr_args})

    log.info('Processamento OCR finalizado com sucesso!')

    cb = partial(ack_message, delivery_tag=method.delivery_tag,
                 routing_key=Queues.PROCESSED.value, message=body)
    connection.add_callback_threadsafe(cb)


def on_document_to_process_thread_handler(channel: BlockingChannel, method: Basic.Deliver, properties: BasicProperties, body: Union[str, bytes], threads: List[Thread]):
    # this is implemented with threads because when the processing takes longer than 60 seconds,
    # rabbitmq closes the connection with error 'missing heartbeats'
    # https://stackoverflow.com/questions/51752890/how-to-disable-heartbeats-with-pika-and-rabbitmq
    t = Thread(target=on_document_to_process, args=(
        channel, method, properties, body))
    t.start()
    threads.append(t)
