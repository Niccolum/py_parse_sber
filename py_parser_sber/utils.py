import datetime
import string
from urllib.parse import urlparse, parse_qsl
from urllib.error import URLError
from typing import Optional, Callable, List, Dict, Any


def check_authorization(f: Callable):
    def wrapper(self, *args: List[Any], **kwargs: Dict[Any, Any]):
        if getattr(self, 'main_menu_link') is None:
            raise NameError('main_menu_link in not found. Are you authenticate?')
        return f(self, *args, **kwargs)
    return wrapper


class ElementHasCss:
    """
    An expectation for checking that an element has a particular css style.
    locator - used to find the element
    returns the WebElement once it has the particular css class
    """
    def __init__(self, locator, css_key, css_val):
        self.locator = locator
        self.css_key = css_key
        self.css_val = css_val

    def __call__(self, driver):
        element = driver.find_element(*self.locator)   # Finding the referenced element
        if element.value_of_css_property(self.css_key) == self.css_val:
            return element
        else:
            return False


def replace_formatter(currency: str, delete_symbols: Optional[str]=None, custom: Optional[dict]=None) -> str:
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


def uri_validator(x: str):
    try:
        url_scheme = urlparse(x)
    except Exception as err:
        raise URLError('Bad URL') from err
    else:
        if not all([url_scheme.scheme, url_scheme.netloc, url_scheme.path]):
            raise URLError('Bad URL')
        return x


def get_query_attr(url: str, attr: str):
    query = urlparse(url).query
    attrs_dict = dict(parse_qsl(query))
    return attrs_dict.get(attr)
