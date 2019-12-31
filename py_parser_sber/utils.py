"""File with small helper functions."""

import datetime
import logging
import os
import string
import time
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Type,
)
from urllib.error import URLError
from urllib.parse import (
    parse_qsl,
    urlparse,
)


logger = logging.getLogger(__name__)


def check_authorization(f: Callable):
    """Check if user log in success."""
    def wrapper(self, *args: List[Any], **kwargs: Dict[Any, Any]):
        if getattr(self, 'main_menu_link', None) is None:
            logger.error('main_menu_link is not found.')
            raise NameError('Are you authenticate?')
        return f(self, *args, **kwargs)
    return wrapper


def replace_formatter(currency: str, delete_symbols: Optional[str] = None, custom: Optional[dict] = None) -> str:
    """Replace unnecessary symbols."""
    if delete_symbols is None:
        delete_symbols = string.punctuation
    translation_table = dict.fromkeys(map(ord, delete_symbols), None)
    if isinstance(custom, dict):
        translation_table.update(str.maketrans(custom))
    return currency.translate(translation_table)


def currency_converter(currency: str, delete_symbols: Optional[str] = None):
    """Convert currency to a single format."""
    formatted_currency = replace_formatter(currency=currency, delete_symbols=delete_symbols)
    currency_dict = {
        'РУБ': 'RUB',
        'ЕВРО': 'EUR',
        'ДОЛЛАР США': 'USD'
    }
    curr = formatted_currency.upper()
    return currency_dict.get(curr, curr)


def sber_time_format(datetime_obj: datetime.datetime):
    """Format datetime to sber-like."""
    return format(datetime_obj, '%d%m%Y')


def uri_validator(x: str) -> str:
    """Validate uri by contain scheme and netloc."""
    try:
        url_scheme = urlparse(x)
    except Exception as err:
        logger.error(x)
        logger.exception(err, exc_info=True)
        raise URLError('Bad URL') from err
    else:
        need_url_parameters = ['scheme', 'netloc']
        if not all(getattr(url_scheme, arg) for arg in need_url_parameters):
            logger.error(x)
            not_found_parameters = [f'{arg} not found' for arg in need_url_parameters
                                    if not getattr(url_scheme, arg)]
            logger.error(f'Bad URL: {", ".join(not_found_parameters)}')
            raise URLError('Bad URL')
        return x


def get_query_attr(url: str, attr: str) -> Optional[str]:
    """Get query attr."""
    query = urlparse(url).query
    attrs_dict = dict(parse_qsl(query))
    return attrs_dict.get(attr)


def get_transaction_interval() -> int:
    """Get default interval between transactions checks."""
    hours = int(os.environ.get('HOURS', 0))
    days = int(os.environ.get('DAYS', 0))
    interval = datetime.timedelta(hours=hours, days=days)
    return int(interval.total_seconds()) or 60 * 60 * 24  # default one day


class Retry:
    """Class, which implements retrying mechanism for every Callable."""

    def __init__(self, function: Callable, error: Type[Exception], err_msg: str = '', max_attempts: int = 5):
        self.function = function
        self.error = error
        self.err_msg = err_msg
        self.max_attempts = max_attempts

        self._default_timeout = 1
        self._current_timeout = self._default_timeout
        self._current_attempt = 1

    def __call__(self, *args, **kwargs):
        """Call a function until it succeeds or the number of attempts is exceeded."""
        while 1:
            try:
                result = self.function(*args, **kwargs)
                self._clear()
                return result
            except self.error as err:
                if self.err_msg:
                    logger.error(self.err_msg)
                try:
                    self._increment()
                except TimeoutError:
                    # We believe that our attempts are exhausted. Try after main interval
                    logger.exception(err, exc_info=True)
                    raise err

    def _increment(self):
        if self._current_attempt > self.max_attempts:
            self._clear()
            logger.warning('All attempts failed')
            raise TimeoutError('All attempts failed')

        logger.info(f'{self._current_attempt}/{self.max_attempts} attempt with timeout {self._current_timeout} ...')
        time.sleep(self._current_timeout)
        self._current_timeout *= 2
        self._current_attempt += 1

    def _clear(self):
        self._current_timeout = self._default_timeout
        self._current_attempt = 1
