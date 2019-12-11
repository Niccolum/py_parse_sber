import os
from pathlib import Path
import json
import time
import logging
import logging.config

from dotenv import load_dotenv

from py_parser_sber.utils import get_transaction_interval
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

def main():
    setup_logging()
    load_env_vars()

    try:
        runner()
    except Exception as err:
        logger.exception(err, exc_info=True)


def main_loop():
    setup_logging()
    load_env_vars()

    while 1:
        try:
            runner()
            time.sleep(get_transaction_interval())
        except Exception as err:
            logger.exception(err, exc_info=True)
            break

if __name__ == '__main__':
    main()