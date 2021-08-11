import tempfile
import logging
import os
import asyncio

import ocrmypdf

from telethon import TelegramClient, events, custom

def log_config():
    formatter_str = '%(asctime)s [%(levelname)s] %(name)s (%(lineno)s): %(message)s'
    formatter = logging.Formatter(formatter_str)
    logging.basicConfig(format=formatter_str)

    log = logging.getLogger()
    ocrmypdf_log = logging.getLogger('ocrmypdf')
    pdfminer_log = logging.getLogger('pdfminer')

    try:
        os.mkdir('logs')
    except:
        pass
    info_file = logging.FileHandler('logs/infos.log')
    info_file.setLevel(logging.INFO)
    info_file.setFormatter(formatter)
    warning_file = logging.FileHandler('logs/warnings.log')
    warning_file.setLevel(logging.WARN)
    warning_file.setFormatter(formatter)
    errors_file = logging.FileHandler('logs/errors.log')
    errors_file.setLevel(logging.ERROR)
    errors_file.setFormatter(formatter)

    log.setLevel(logging.INFO)
    log.addHandler(info_file)
    log.addHandler(warning_file)
    log.addHandler(errors_file)
    ocrmypdf_log.setLevel(logging.WARN)
    ocrmypdf_log.addHandler(warning_file)
    ocrmypdf_log.addHandler(errors_file)
    pdfminer_log.setLevel(logging.ERROR)
    pdfminer_log.addHandler(errors_file)

    return log

log = log_config()

api_id = int(os.getenv('TELEGRAM_API_ID'))
api_hash = os.getenv('TELEGRAM_API_HASH')
bot_token = os.getenv('TELEGRAM_BOT_TOKEN')

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

def main():
    with TelegramClient('name', api_id, api_hash).start(bot_token=bot_token) as client:
        @client.on(events.NewMessage(incoming=True, pattern='/start'))
        async def start_command(event: events.newmessage.NewMessage.Event):
            message_obj: custom.message.Message = event.message
            
            await message_obj.respond('Olá! Meu nome é Pytonisa e posso transformar pdfs em pdfs acessíveis/pesquisáveis (em OCR)')
            await message_obj.respond('Tenha em mente que pdfs grandes (em tamanho ou qtd de páginas) podem demorar a serem processados e, se já possuírem algum OCR, vai demorar ainda mais, pois será necessário limpar o OCR anterior')
            await message_obj.respond('Para definir a(s) língua(s) do documento, utilize o comando -l lang1+lang2+lang3 no texto da mensagem do documento')
            await message_obj.respond('No momento, estão disponíveis as línguas português (por), inglês (eng) e espanhol (spa)')
            await message_obj.respond('Exemplo de comando: `-l por+eng`')
            await message_obj.respond('O código fonte pode ser encontrado em https://github.com/LuisF3')
            await message_obj.respond('Se quiser, você pode doar uma quantia pelo pix. A chave aleatória é: 5edf6e87-8c5b-4cb9-b584-6ec1f12c8cbe')


        @client.on(events.NewMessage(incoming=True, pattern='(^-)|(^$)', func=lambda e: e.file is not None and e.file.ext == '.pdf'))
        async def pdf_to_ocr(event: events.newmessage.NewMessage.Event):
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
                    'output_file': message_obj.file.name,
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

                default_args['input_file'] = await message_obj.download_media()

                loop = asyncio.get_event_loop()
                log.info('Iniciando processamento OCR')
                await message_obj.respond('Iniciando processamento OCR!')
                try:
                    await loop.run_in_executor(None, lambda : ocrmypdf.ocr(**default_args))
                except ocrmypdf.PriorOcrFoundError:
                    log.info('Arquivo já possui OCR')
                    default_args['deskew'] = False
                    default_args['clean-final'] = False
                    default_args['remove-background'] = False
                    default_args['redo_ocr'] = True
                    await loop.run_in_executor(None, lambda : ocrmypdf.ocr(**default_args))
                except ocrmypdf.MissingDependencyError as mde:
                    log.error('Não foi possível processar alguma das línguas solicitadas', mde)
                    await message_obj.reply('Não foi possível processar alguma das línguas solicitadas')
                    raise mde
                except Exception as e:
                    log.error('Ocorreu um erro desconhecido', e)
                    raise e


                await message_obj.respond('OCR feito! Estamos fazendo upload do seu arquivo')
                with open(default_args['output_file'], 'rb') as file:
                    await message_obj.reply('Aqui está!', file=file)
            log.info('Finalizado')

        log.info('Bot initiated')
        client.run_until_disconnected()

if __name__ == '__main__':
    try:
        main()
    except:
        print('entrou')
        log.exception('Uncaugh exception...')
