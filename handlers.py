import tempfile
import os

from telethon import events, custom
from aio_pika import Channel, Message

from logs import log

async def start_command(event: events.newmessage.NewMessage.Event):
    message_obj: custom.message.Message = event.message

    await message_obj.respond('Olá! Meu nome é Pytonisa e posso transformar pdfs em pdfs acessíveis/pesquisáveis (em OCR)')
    await message_obj.respond('Tenha em mente que pdfs grandes (em tamanho ou qtd de páginas) podem demorar a serem processados e, se já possuírem algum OCR, vai demorar ainda mais, pois será necessário limpar o OCR anterior')
    await message_obj.respond('Para mais informações, veja as opções do bot (ou digite \'/\')')
    await message_obj.respond('Se quiser, você pode doar uma quantia pelo pix. A chave aleatória é: 5edf6e87-8c5b-4cb9-b584-6ec1f12c8cbe')

async def help_lang_command(event: events.newmessage.NewMessage.Event):
    message_obj: custom.message.Message = event.message
    
    await message_obj.respond('Para definir a(s) língua(s) do documento, utilize o comando `-l lang1+lang2+lang3` no texto da mensagem do documento')
    await message_obj.respond('No momento, estão disponíveis as línguas português (por), inglês (eng) e espanhol (spa), mas, pode me contatar se precisar de outro idioma (https://t.me/Luis_pi)')
    await message_obj.respond('Exemplo de comando: `-l por+eng` - Reconhece um documento com texto misto de inglês e português')

async def more_info_command(event: events.newmessage.NewMessage.Event):
    message_obj: custom.message.Message = event.message
    
    await message_obj.respond('O código fonte pode ser encontrado em https://github.com/LuisF3')
    await message_obj.respond('Se quiser, você pode doar uma quantia pelo pix. A chave aleatória é: 5edf6e87-8c5b-4cb9-b584-6ec1f12c8cbe')

async def pdf_to_ocr(rabbitmq, event: events.newmessage.NewMessage.Event):
    print(rabbitmq)
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

    with tempfile.TemporaryDirectory() as path:
        default_args = {
            'input_file': None,
            'output_file': os.path.join(path, message_obj.file.name),
            'language': ['por'],
            'deskew': True,
            'rotate_pages': True,
            'clean': False,
            'optimize': 1,
            'progress_bar': False
        }

        langs = get_flags(message_obj.message, '-l', '+')
        if len(langs) > 0:
            log.info('Language set to: ' + ' '.join(langs))
            default_args['language'] = langs

        default_args['input_file'] = await message_obj.download_media(file=path)

        log.info('Inserindo o arquivo na fila')
        await message_obj.respond('Inserindo o arquivo na fila')

        channel: Channel = rabbitmq['channel']

        await channel.default_exchange.publish(Message(bytes(default_args['input_file'], 'latin1')), routing_key='hello')
        
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
