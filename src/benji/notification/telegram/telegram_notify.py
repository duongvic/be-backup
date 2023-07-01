import telegram
from benji.logging import logger


class TelegramNotify:
    def __init__(self, config):
        self.token = config.get('telegram_token')
        self.chat_id = config.get('telegram_group_id')
        self.bot = telegram.Bot(self.token)

    def send_message(self, msg):
        try:
            self.bot.send_message(chat_id=self.chat_id, text=msg, parse_mode='Markdown')
        except Exception as e:
            logger.error('Telegram error occurred: ' + str(e))
            return False
        return True
