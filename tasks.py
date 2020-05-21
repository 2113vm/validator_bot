from invoke import task

from bot import Bot
from metrics import Validator


@task
def run_telegram_bot(cfg):
    Bot(token=cfg.telegram_bot.token,
        proxy_url=cfg.telegram_bot.proxy_url,
        proxy_kwargs=cfg.telegram_bot.proxy_kwargs,
        validator=Validator()).run()
