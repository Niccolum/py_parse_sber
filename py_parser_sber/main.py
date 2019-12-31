import os
from pathlib import Path
import json
import time
import logging
import logging.config

from py_parser_sber.utils import get_transaction_interval, Retry
from py_parser_sber.sberbank_parse import SberbankClientParser


logger = logging.getLogger(__name__)


def setup_logging(logging_path='logging.json'):
    curr_dir = Path(__file__).resolve().parents[0]
    with curr_dir.joinpath(logging_path).open() as f:
        config = json.load(f)
    logging.config.dictConfig(config)


def runner():
    logger.info('Start parsing...')
    need_env_vars = ['LOGIN', 'PASSWORD', 'SERVER_URL', 'SEND_ACCOUNT_URL', 'SEND_PAYMENT_URL']
    need_data_for_start = {k.lower(): os.environ[k] for k in need_env_vars}

    need_data_for_start['transactions_interval'] = get_transaction_interval()
    need_data_for_start['server_port'] = os.getenv('SERVER_PORT', 80)
    need_data_for_start['server_scheme'] = os.getenv('SERVER_SCHEME', 'http')

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

    retry = Retry(function=runner, error=Exception, max_attempts=2)
    retry()


def py_parser_sber_run_infinite():
    setup_logging()

    retry = Retry(function=runner, error=Exception, max_attempts=3)
    while 1:
        try:
            retry()
        finally:
            hours = os.getenv("HOURS", 0)
            days = os.getenv("DAYS", 0 if hours else 1)
            logger.info(f'Waiting for a new transactions after {days} days and {hours} hours')

            time.sleep(get_transaction_interval())


if __name__ == '__main__':
    py_parser_sber_run_once()
