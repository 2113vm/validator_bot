import logging
from pathlib import Path
from shutil import rmtree
from zipfile import ZipFile

from telegram.ext import CommandHandler, Filters, MessageHandler, Updater


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)


class Bot:
    def __init__(self, token,
                 proxy_url,
                 proxy_kwargs,
                 cig_ocr_validator,
                 pricetag_ocr_validator,
                 cig_text_detection_validator,
                 pricetag_text_detection_validator):

        self.cig_ocr_validator = cig_ocr_validator
        self.cig_text_detection_validator = cig_text_detection_validator
        self.pricetag_ocr_validator = pricetag_ocr_validator
        self.pricetag_text_detection_validator = pricetag_text_detection_validator

        self.updater = Updater(token,
                               request_kwargs={'proxy_url': proxy_url,
                                               'urllib3_proxy_kwargs': proxy_kwargs})
        self.dispatcher = self.updater.dispatcher

        start_handler = CommandHandler('start', self.start)
        help_handler = CommandHandler('help', self.help)
        metric_handler = MessageHandler(Filters.document, self.get_metrics)

        self.dispatcher.add_handler(start_handler)
        self.dispatcher.add_handler(help_handler)
        self.dispatcher.add_handler(metric_handler)

        pass

    @staticmethod
    def start(bot, update):
        bot.send_message(chat_id=update.effective_chat.id, text="I'm a metric bot, please send me files!")

    @staticmethod
    def help(bot, update):

        instruction = """
        Это инструкция использования
        
        Если ты хочешь провалидировать детекцию текста, то отправь архив с предсказаниями. 
        К архиву добавь подпись: "cig" или "pricetag"
        
        На какую структуру расчитано?
        results/ # название папки не имеет значение
            cig_name1.txt # файл должен содержать исходное название файла (названия могут быть не равны). 
                4,11,62,11,62,25,4,25 # line 1
                4,11,62,11,62,25,4,25 # line 2
                ...
            cig_name2.txt
                ...
            ...
            
        Если ты хочешь провалидировать оср, то отправиь .txt или .csv файл.
        К файлу добавь подпись: "cig" или "pricetag"
        
        Структура .txt или .csv файла
        
            img_name любой текст # разделение между img_name и любой текст может быть табуляция или пробел 
            img_name1 любой текст1
        ...
        """

        bot.send_message(chat_id=update.effective_chat.id, text=instruction)

    def get_metrics(self, bot, update):
        logging.info('got files')
        mode = update.message.caption
        file_id = update.message.document['file_id']
        file = bot.getFile(file_id)
        filename = Path(Path(file.file_path).name)
        _ = file.download(Path(file.file_path).name)
        if filename.suffix in ['.txt', '.csv']:
            if mode == 'cig':
                r = self.cig_ocr_validator.validate(filename)
            else:
                r = self.pricetag_ocr_validator.validate(filename)
        else:
            with ZipFile(filename) as zip:
                zip.extractall(f'./zip_tmp/{filename}')
            d = list(filter(lambda p: not str(p.name).startswith('.'),
                            list(Path(f'./zip_tmp/{filename}').iterdir())))[0]
            dir_path = Path(f'./zip_tmp/{filename}/{d.name}')
            if mode == 'cig':
                r = self.cig_text_detection_validator.validate(dir_path)
            else:
                r = self.pricetag_text_detection_validator.validate(dir_path)
            rmtree(f'./zip_tmp/{filename}')
        Path(filename).unlink()
        bot.send_message(chat_id=update.effective_chat.id, text=str(r))

    def run(self):
        logging.info('Application has started')
        self.updater.start_polling()
        self.updater.idle()
