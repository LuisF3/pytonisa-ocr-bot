import tempfile
import asyncio
import os

import ocrmypdf

from telethon import events, custom

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
