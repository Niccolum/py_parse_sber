"""
Abstract realization of ClientParser, Account parser and Transaction parser.

Based on them, you can build your own parsers of other banks.
"""

import abc
import json
import logging
import socket
import time
import uuid
from collections import namedtuple
from typing import (
    ClassVar,
    Dict,
    Iterator,
    List,
    Optional,
    Type,
    Union,
)

import requests
from requests.exceptions import ConnectionError

from selenium import webdriver
from selenium.common.exceptions import TimeoutException as SeleniumTimeoutException
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait

from py_parser_sber.utils import (
    Retry,
    uri_validator,
)


logger = logging.getLogger(__name__)

TIMEOUT = 30
Transaction = namedtuple('Transaction', ['id', 'transaction'])


class AbstractAccount(abc.ABC):  # noqa H601
    """AbstractAccount have parser class abstractmethod and save his values, as result of this parser."""

    acc_type: ClassVar[str]

    def __init__(self, name: str, funds: str, currency: str, account_id: str):
        self.name = name
        self.funds = funds
        self.currency = currency
        self.account_id = account_id

    @classmethod
    @abc.abstractmethod
    def account_parser(cls, raw_account: WebElement) -> Type['AbstractAccount']:
        """Get raw parsed data (strings) and create, based on it, own class."""

    @property
    def account(self) -> Dict[str, str]:
        """
        Get account data.

        .copy() for only read this parameter.
        """
        return vars(self).copy()

    def to_json(self):
        """Return data for api, BudgetTracker compatible."""
        return {
            'name': self.name,
            'value': self.funds,
            'ccy': self.currency
        }


class AbstractTransaction(abc.ABC):  # noqa H601
    """AbstractTransaction have parser class abstractmethod and save his values, as result of this parser."""

    def __init__(self, order_id: str, account_name: str, tr_time: str, cost: str, currency: str, description: str):
        self.order_id = order_id
        self.account_name = account_name
        self.tr_time = tr_time
        self.cost = cost
        self.currency = currency
        self.description = description

    def __repr__(self):  # noqa D105
        return '{class_name}({params})'.format(
            class_name=self.__class__.__name__,
            params=', '.join(f"{k}='{v}'" for k, v in vars(self).items()))

    @classmethod
    @abc.abstractmethod
    def transaction_parser(
            cls,
            raw_transaction: WebElement,
            account: Type[AbstractAccount]
    ) -> Iterator[Optional[Type['AbstractTransaction']]]:
        """Get raw parsed data (strings) and create, based on it, own class."""

    @property
    def raw_transaction(self) -> dict:
        """
        Get account data.

        .copy() for only read this parameter.
        """
        return vars(self).copy()

    @property
    def transaction_id(self) -> str:
        """Create unique id of transaction, if it not exist."""
        return uuid.uuid5(uuid.NAMESPACE_X500, repr(self)).hex

    def to_json(self):
        """Return data for api, BudgetTracker compatible."""
        return {
            'id': self.transaction_id,
            'account': self.account_name,
            'when': self.tr_time,
            'amount': self.cost,
            'currency': self.currency,
            'what': self.description
        }


class AbstractClientParser(abc.ABC):  # noqa H601
    """
    Abstract client with main logic.

    It emulate user - log in, get info, pass it to parsers and send to another server.
    """

    main_page: str

    def __init__(self, login: str, password: str, transactions_interval: int,
                 server_url: str, server_scheme: str, server_port: str,
                 send_account_url: str, send_payment_url: str) -> None:

        self.main_page = uri_validator(type(self).main_page)
        self.login = login
        self.password = password
        self.transactions_interval = transactions_interval

        self.driver = self._prepare_webdriver()
        self._container: Dict[AbstractAccount, List[Optional[AbstractTransaction]]] = {}

        self.server_url = uri_validator(f'{server_scheme}://{socket.gethostbyname(server_url)}:{server_port}')
        self.send_account_url = f'{self.server_url}{send_account_url}'
        self.send_payment_url = f'{self.server_url}{send_payment_url}'

    @staticmethod
    def _prepare_webdriver():
        options = Options()
        options.headless = True

        driver = webdriver.Firefox(options=options)
        driver.set_page_load_timeout(TIMEOUT)
        return driver

    def wait_click_redirect(self, click_item: WebElement) -> None:
        """Wait clicked element redirect."""
        current_url = self.driver.current_url

        def main_logic():
            click_item.click()
            start_time = time.monotonic()
            WebDriverWait(self.driver, TIMEOUT).until(expected_conditions.url_changes(current_url))
            end_time = time.monotonic() - start_time
            logger.info(f'Success redirect from {current_url} to {self.driver.current_url} '
                        f'by {end_time:.2f} seconds')

        retry = Retry(
            function=main_logic,
            error=SeleniumTimeoutException,
            err_msg=(f'Error. Old url: {current_url} has not changed to '
                     f'{self.driver.current_url} with timeout {TIMEOUT}'),
            max_attempts=5
        )
        try:
            retry()
        except SeleniumTimeoutException as exc:
            self.close()
            raise SeleniumTimeoutException from exc

    def get(self, url: str):
        """Get method, wrapped by Retry mechanism."""
        def main_logic():
            start_time = time.monotonic()
            self.driver.get(url)
            end_time = time.monotonic() - start_time
            logger.info(f"Success loading page: {url} by {end_time:.2f} seconds")

        retry = Retry(
            function=main_logic,
            error=SeleniumTimeoutException,
            err_msg=f"Couldn't load page {url} with timeout {TIMEOUT}",
            max_attempts=5
        )
        try:
            retry()
        except SeleniumTimeoutException as exc:
            logger.debug(exc, exc_info=True)
            self.close()
            raise SeleniumTimeoutException from exc

    @abc.abstractmethod
    def auth(self) -> None:
        """Authenticate in bank client WebGUI."""

    @abc.abstractmethod
    def accounts_page_parser(self) -> None:
        """Parse info about bank accounts (like Bank Account or Card Bank Account)."""

    @abc.abstractmethod
    def transactions_pages_parser(self) -> None:
        """Parse page with transactions (payments, receipts and etc.)."""

    @staticmethod
    def _send_request(url: str, data: Union[Dict, List]) -> None:
        headers = {'content-type': 'application/json'}
        retry = Retry(
            function=requests.post,
            error=ConnectionError,
            err_msg=f'request to url {url} not sending',
            max_attempts=3
        )
        r = retry(url=url, data=json.dumps(data), headers=headers)
        if r.status_code != 200:
            logger.warning(f'request to url {url} with data {data} not sending')
            logger.error(r.text)

    def send_account_data(self) -> None:
        """Send bank account data (AbstractAccount) to send_account_url."""
        data = [acc.to_json() for acc in self._container.keys()]
        self._send_request(url=self.send_account_url, data=data)

    def send_payment_data(self) -> None:
        """Send bank payment data (AbstractTransaction) to send_account_url."""
        data = [tr.to_json() for acc_tr in self._container.values() for tr in acc_tr if tr is not None]
        if data:
            self._send_request(url=self.send_payment_url, data=data)
        else:
            logger.info('No transactions data for last time')

    def close(self) -> None:
        """Graceful shutdown."""
        logger.info('Force closing the web driver ...')
        self.driver.quit()
        self._container.clear()
        logger.debug('Done')
