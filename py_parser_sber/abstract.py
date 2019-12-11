import abc
import uuid
import json
import time
from typing import Optional, Iterator, Dict, Type, Union, List, ClassVar
from collections import namedtuple
import logging

import requests
from selenium import webdriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.firefox.options import Options

from py_parser_sber.utils import uri_validator


logger = logging.getLogger(__name__)

TIMEOUT = 30
Transaction = namedtuple('Transaction', ['id', 'transaction'])


class AbstractAccount(abc.ABC):
    acc_type: ClassVar[str]

    def __init__(self, name: str, funds: str, currency: str, account_id: str):
        self.name = name
        self.funds = funds
        self.currency = currency
        self.account_id = account_id

    def __repr__(self):
        return '{class_name}({params})'.format(
            class_name=self.__class__.__name__,
            params=', '.join(f"{k}='{v}'" for k, v in vars(self).items()))

    @classmethod
    @abc.abstractmethod
    def account_parser(cls, raw_account: WebElement) -> Type['AbstractAccount']:
        """
        get raw parsed data (strings) and create, based on it, own class
        """

    @property
    def account(self) -> Dict[str, str]:
        """
        Get account data
        .copy() for only read this parameter
        """
        return vars(self).copy()

    def to_json(self):
        return {
            'name': self.name,
            'value': self.funds,
            'ccy': self.currency
        }


class AbstractTransaction(abc.ABC):

    def __init__(self, order_id: str, account_name: str, tr_time: str, cost: str, currency: str, description: str):
        self.order_id = order_id
        self.account_name = account_name
        self.tr_time = tr_time
        self.cost = cost
        self.currency = currency
        self.description = description

    def __repr__(self):
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
        """
        get transaction data
        """

    @property
    def raw_transaction(self) -> dict:
        """
        Get account data
        .copy() for only read this parameter
        """
        return vars(self).copy()

    @property
    def transaction_id(self) -> str:
        return uuid.uuid5(uuid.NAMESPACE_X500, repr(self)).hex

    def to_json(self):
        return {
            'id': self.transaction_id,
            'account': self.account_name,
            'when': self.tr_time,
            'amount': self.cost,
            'currency': self.currency,
            'what': self.description
        }


class AbstractClientParser(abc.ABC):
    main_page: str

    def __init__(self, login: str, password: str, 
                 server_url: str, send_account_url: str, send_payment_url: str, 
                 transactions_interval: int) -> None:

        self.main_page = uri_validator(type(self).main_page)
        self.login = login
        self.password = password
        self.driver = self._prepare_webdriver()
        self._container: Dict[AbstractAccount, List[Optional[Type[AbstractTransaction]]]] = {}
        self.send_account_url = uri_validator(server_url + send_account_url)
        self.send_payment_url = uri_validator(server_url + send_payment_url)
        self.transactions_interval = transactions_interval

    @staticmethod
    def _prepare_webdriver():
        options = Options()
        options.headless = True

        driver = webdriver.Firefox(options=options)
        driver.set_page_load_timeout(TIMEOUT)
        return driver

    def wait_click_redirect(self, click_item: WebElement) -> None:
        """
        wait clicked element redirect
        """
        current_url = self.driver.current_url
        click_item.click()
        try:
            start_time = time.monotonic()
            WebDriverWait(self.driver, TIMEOUT).until(EC.url_changes(current_url))
            end_time = time.monotonic() - start_time
            logger.info(f'Success redirect from {current_url} to {self.driver.current_url} by {end_time:.2f} seconds')
        except TimeoutException as exc:
            logger.error(f'Error. Old url: {current_url} has not changed to '
                         f'{self.driver.current_url} with timeout {TIMEOUT}')
            logger.exception(exc, exc_info=True)
            self.close()
            raise TimeoutException from exc

    def get(self, url: str):
        try:
            start_time = time.monotonic()
            self.driver.get(url)
            end_time = time.monotonic() - start_time
            logger.info(f"Success loading page: {url} by {end_time:.2f} seconds")
        except TimeoutException as exc:
            logger.error(f"Couldn't load page {url} with timeout {TIMEOUT}")
            logger.exception(exc, exc_info=True)
            self.close()
            raise TimeoutException from exc

    @abc.abstractmethod
    def auth(self) -> None:
        """
        authenticate in bank client WebGUI
        """

    @abc.abstractmethod
    def accounts_page_parser(self) -> None:
        """
        parse info about bank accounts (like Bank Account or Card Bank Account)
        """

    @abc.abstractmethod
    def transactions_pages_parser(self) -> None:
        """
        parse page with transactions (payments, receipts and etc.)
        """

    @staticmethod
    def _send_request(url: str, data: Union[Dict, List]) -> None:
        headers = {'content-type': 'application/json'}
        r = requests.post(url=url, data=json.dumps(data), headers=headers)
        if r.status_code != 200:
            logger.warning('request not sending')
            logger.info(r.text)

    def send_account_data(self) -> None:
        data = [acc.to_json() for acc in self._container.keys()]
        self._send_request(url=self.send_account_url, data=data)

    def send_payment_data(self) -> None:
        data = [tr.to_json() for acc_tr in self._container.values() for tr in acc_tr]
        self._send_request(url=self.send_payment_url, data=data)

    def close(self) -> None:
        self.driver.quit()
        self._container.clear()
