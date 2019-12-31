import os
from pathlib import Path
import json
import time
import logging
import logging.config

from dotenv import load_dotenv

from py_parser_sber.utils import get_transaction_interval, Retry
from py_parser_sber.sberbank_parse import SberbankClientParser


logger = logging.getLogger(__name__)


def setup_logging(logging_path='logging.json'):
    curr_dir = Path(__file__).resolve().parents[0]
    with curr_dir.joinpath(logging_path).open() as f:
        config = json.load(f)
    logging.config.dictConfig(config)


def load_env_vars():
    project_dir = Path(__file__).resolve().parents[1]
    load_dotenv(project_dir.joinpath('.env'))


def runner():
    logger.info('Start parsing...')
    need_env_vars = ['LOGIN', 'PASSWORD', 'SERVER_URL', 'SEND_ACCOUNT_URL', 'SEND_PAYMENT_URL']
    need_data_for_start = {k.lower(): os.environ[k] for k in need_env_vars}

    need_data_for_start['transactions_interval'] = get_transaction_interval()

    sber = SberbankClientParser(**need_data_for_start)
    try:
        sber.auth()
        sber.accounts_page_parser()
        sber.transactions_pages_parser()
        sber.send_account_data()
        sber.send_payment_data()
        logger.info('Success iteration')
    finally:
        sber.close()


def py_parser_sber_run_once():
    setup_logging()
    load_env_vars()

    retry = Retry(function=runner, error=Exception, max_attempts=2)
    retry()


def py_parser_sber_run_infinite():
    setup_logging()
    load_env_vars()

    retry = Retry(function=runner, error=Exception, max_attempts=3)
    while 1:
        try:
            retry()
        finally:
            time.sleep(get_transaction_interval())


if __name__ == '__main__':
    py_parser_sber_run_once()
