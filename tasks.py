from invoke import task

from bot import Bot
from metrics import OCRValidator, TextDetectionValidator


@task
def run_telegram_bot(cfg):
    Bot(token=cfg.telegram_bot.token,
        proxy_url=cfg.telegram_bot.proxy_url,
        proxy_kwargs=cfg.telegram_bot.proxy_kwargs,
        cig_ocr_validator=OCRValidator(cfg.ocr.cig.gt_path),
        pricetag_ocr_validator=OCRValidator(cfg.ocr.pricetag.gt_path),
        cig_text_detection_validator=TextDetectionValidator(cfg.text_detection.cig.gt_path),
        pricetag_text_detection_validator=TextDetectionValidator(cfg.text_detection.pricetag.gt_path)).run()
