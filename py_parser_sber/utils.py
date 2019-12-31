import os
import datetime
import string
import logging
import time
import socket
from urllib.parse import urlparse, parse_qsl
from urllib.error import URLError
from typing import Optional, Callable, List, Dict, Any


logger = logging.getLogger(__name__)


def check_authorization(f: Callable):
    def wrapper(self, *args: List[Any], **kwargs: Dict[Any, Any]):
        if getattr(self, 'main_menu_link') is None:
            logger.error('main_menu_link is not found.')
            raise NameError('Are you authenticate?')
        return f(self, *args, **kwargs)
    return wrapper


def replace_formatter(currency: str, delete_symbols: Optional[str] = None, custom: Optional[dict] = None) -> str:
    """
    replace unnecessary symbols
    """
    if delete_symbols is None:
        delete_symbols = string.punctuation
    translation_table = dict.fromkeys(map(ord, delete_symbols), None)
    if isinstance(custom, dict):
        translation_table.update(str.maketrans(custom))
    return currency.translate(translation_table)


def currency_converter(currency: str, delete_symbols: Optional[str] = None):
    """
    Converting to a single format
    """
    formatted_currency = replace_formatter(currency=currency, delete_symbols=delete_symbols)
    currency_dict = {
        'РУБ': 'RUB',
        'ЕВРО': 'EUR',
        'ДОЛЛАР США': 'USD'
    }
    curr = formatted_currency.upper()
    return currency_dict.get(curr, curr)


def sber_time_format(datetime_obj: datetime.datetime):
    return format(datetime_obj, '%d%m%Y')


def uri_validator(x: str) -> str:
    try:
        url_scheme = urlparse(x)
    except Exception as err:
        logger.error(x)
        logger.exception(err, exc_info=True)
        raise URLError('Bad URL') from err
    else:
        need_url_parameters = ['scheme', 'netloc', 'path']
        if not all(getattr(url_scheme, arg) for arg in need_url_parameters):
            try:
                socket.gethostbyname(x)
            except socket.gaierror:
                logger.error(x)
                not_found_parameters = [f'{arg} not found' for arg in need_url_parameters
                                        if not getattr(url_scheme, arg)]
                logger.error(f'Bad URL: {", ".join(not_found_parameters)}')
                raise URLError('Bad URL')
        return x


def get_query_attr(url: str, attr: str) -> str:
    query = urlparse(url).query
    attrs_dict = dict(parse_qsl(query))
    return attrs_dict.get(attr)


def get_transaction_interval() -> int:
    hours = int(os.environ.get('HOURS', 0))
    days = int(os.environ.get('DAYS', 0))
    interval = datetime.timedelta(hours=hours, days=days)
    return interval.total_seconds() or 60 * 60 * 24  # default one day


class Retry:
    def __init__(self, function, error, err_msg='', max_attempts=5):
        self.function = function
        self.error = error
        self.err_msg = err_msg
        self.default_timeout = 1
        self.max_attempts = max_attempts
        self.current_timeout = self.default_timeout
        self.current_attempt = 1

    def __call__(self, *args, **kwargs):
        while 1:
            try:
                result = self.function(*args, **kwargs)
                self.clear()
                return result
            except self.error as err:
                if self.err_msg:
                    logger.error(self.err_msg)
                try:
                    self.increment()
                except TimeoutError:
                    # We believe that our attempts are exhausted. Try after main interval
                    logger.exception(err, exc_info=True)
                    raise err

    def increment(self):
        if self.current_attempt > self.max_attempts:
            self.clear()
            logger.warning('All attempts failed')
            raise TimeoutError('All attempts failed')

        logger.info(f'{self.current_attempt}/{self.max_attempts} attempt with timeout {self.current_timeout} ...')
        time.sleep(self.current_timeout)
        self.current_timeout *= 2
        self.current_attempt += 1

    def clear(self):
        self.current_timeout = self.default_timeout
        self.current_attempt = 1
