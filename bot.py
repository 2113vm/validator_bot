import logging

from telegram.ext import CommandHandler, Filters, MessageHandler, Updater

from metrics import Validator

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)


class Bot:
    def __init__(self, token, proxy_url, proxy_kwargs, validator: Validator):

        self.validator = validator
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
        bot.send_message(chat_id=update.effective_chat.id, text="I'm a metric bot, please send me files!")

    @staticmethod
    def get_metrics(bot, update):
        pass

    def run(self):
        logging.info('Application has started')
        self.updater.start_polling()
        self.updater.idle()
