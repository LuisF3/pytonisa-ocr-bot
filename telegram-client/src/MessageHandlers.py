from objects.QueueMessage import QueueMessage
import os

from telethon import events, custom
from aio_pika import Channel, Message
from motor.core import Database, Collection
from pymongo.results import InsertOneResult
from bson.objectid import ObjectId

from configs.Logs import log
from objects.Queues import Queues

rabbitmq: dict = None
mongodb_db: Database = None

async def start_command(event: events.newmessage.NewMessage.Event) -> None:
    message_obj: custom.message.Message = event.message

    await message_obj.respond('Olá! Meu nome é Pytonisa e posso transformar pdfs em pdfs acessíveis/pesquisáveis (em OCR)')
    await message_obj.respond('Tenha em mente que pdfs grandes (em tamanho ou qtd de páginas) podem demorar a serem processados e, se já possuírem algum OCR, vai demorar ainda mais, pois será necessário limpar o OCR anterior')
    await message_obj.respond('Para mais informações, veja as opções do bot (ou digite \'/\')')
    await message_obj.respond('Se quiser, você pode doar uma quantia pelo pix. A chave aleatória é: 5edf6e87-8c5b-4cb9-b584-6ec1f12c8cbe')

async def help_lang_command(event: events.newmessage.NewMessage.Event) -> None:
    message_obj: custom.message.Message = event.message
    
    await message_obj.respond('Para definir a(s) língua(s) do documento, utilize o comando `-l lang1+lang2+lang3` no texto da mensagem do documento')
    await message_obj.respond('No momento, estão disponíveis as línguas português (por), inglês (eng) e espanhol (spa), mas, pode me contatar se precisar de outro idioma (https://t.me/Luis_pi)')
    await message_obj.respond('Exemplo de comando: `-l por+eng` - Reconhece um documento com texto misto de inglês e português')

async def more_info_command(event: events.newmessage.NewMessage.Event) -> None:
    message_obj: custom.message.Message = event.message
    
    await message_obj.respond('O código fonte pode ser encontrado em https://github.com/LuisF3')
    await message_obj.respond('Se quiser, você pode doar uma quantia pelo pix. A chave aleatória é: 5edf6e87-8c5b-4cb9-b584-6ec1f12c8cbe')

async def pdf_to_ocr(event: events.newmessage.NewMessage.Event) -> None:
    """Handles messages for applying ocr to a pdf
    
    This function handles incoming new messages that respects the 
    pattern '(^-)|(^$)' (messages that are empty or starts with -)
    and have an attached pdf file.

    Args:
        event (`events.newmessage.NewMessage.Event`):
            The new message event (from telethon)
    """

    message_obj: custom.message.Message = event.message

    log.info('pdf_to_ocr called')
    await message_obj.reply('Arquivo recebido!')

    files_folder = 'pdfs' + os.sep

    default_args = {
        'input_file': None,
        'output_file': files_folder + message_obj.file.name,
        'language': ['por'],
        'deskew': True,
        'rotate_pages': True,
        'clean': False,
        'optimize': 1,
        'progress_bar': False,
    }

    langs = get_flags(message_obj.message, '-l', '+')
    if len(langs) > 0:
        log.info('Language set to: ' + ' '.join(langs))
        default_args['language'] = langs

    default_args['input_file'] = await message_obj.download_media(file=files_folder + message_obj.file.name)
    
    collection: Collection = mongodb_db.ocr_request
    channel: Channel = rabbitmq['channel']

    queue_message = QueueMessage(message_obj.chat_id, message_obj.id, default_args)
    result: InsertOneResult = await collection.insert_one(queue_message.__dict__)
    objectId: ObjectId = result.inserted_id

    encoded_id = bytes(str(objectId), 'utf-8')
    await channel.default_exchange.publish(Message(encoded_id), routing_key=Queues.TO_PROCESS.value)
    
    log.info('Arquivo inserido na fila para processamento')
    await message_obj.respond('Arquivo inserido na fila para processamento')
    log.info('Finalizado')

def get_flags(string: str, flag: str, splitter: str) -> list:
    if flag in string:
        index = string.index(flag)
        lang_args = string[index + 3 : ]
        
        try:
            index = lang_args.index('-')
            lang_args = lang_args[ : index - 1]
        except:
            pass

        return lang_args.split(splitter)
    return []
