import os
from pathlib import Path
import json
import logging
import logging.config

from py_parser_sber.sberbank_parse import SberbankClientParser

logger = logging.getLogger(__name__)


def setup_logging(logging_path='logging.json'):
    curr_dir = Path(__file__).parents[0]
    with curr_dir.joinpath(logging_path).open() as f:
        config = json.load(f)
    logging.config.dictConfig(config)


def main():
    need_env_vars = ['LOGIN', 'PASSWORD', 'SERVER_URL', 'SEND_ACCOUNT_URL', 'SEND_PAYMENT_URL']
    need_data_for_start = {k.lower(): os.environ[k] for k in need_env_vars}

    sber = SberbankClientParser(**need_data_for_start)
    sber.auth()
    sber.account_page_parser_BankAccount()
    sber.account_page_parser_CardAccount()
    sber.transaction_page_parser(interval=60 * 60 * 24 * 30)
    sber.send_account_data()
    sber.send_payment_data()
    logger.debug(sber._container)


if __name__ == '__main__':
    setup_logging()
    while 1:
        try:
            main()
        except Exception as err:
            logger.exception(err, exc_info=True)