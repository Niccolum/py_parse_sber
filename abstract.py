import abc
from typing import Optional, Iterator, Dict, Type, Union, List
from collections import namedtuple

import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from utils import (
    currency_converter,
    replace_formatter,
    get_query_attr,
    uri_validator)


TIMEOUT = 30
Transaction = namedtuple('Transaction', ['id', 'transaction'])


class AbstractAccount(abc.ABC):

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
    def _account_parser(cls, raw_account: WebElement) -> Type['AbstractAccount']:
        """
        get raw parsed data (strings) and create, based on it, own class
        """
        ...

    @property
    def account(self) -> Dict[str, str]:
        """
        Get account data
        .copy() for only read this parameter
        """
        return vars(self).copy()


class AbstractProcessedTransaction(abc.ABC):

    def __init__(self, order_id: str, account_name: str, time: str, cost: str, currency: str, description: str):
        self.order_id = order_id
        self.account_name = account_name
        self.time = time
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
    ) -> Iterator[Optional[Type['AbstractProcessedTransaction']]]:
        ...

    @property
    def raw_transaction(self) -> dict:
        """
        Get account data
        .copy() for only read this parameter
        """
        return vars(self).copy()


class AbstractClientParser(abc.ABC):
    main_page: str

    @abc.abstractmethod
    def __init__(self, login: str, password: str, 
                 server_url: str, send_account_url: str, send_payment_url: str, 
                 transactions_interval: int) -> None:

        self.main_page = uri_validator(type(self).main_page)
        self.login = login
        self.password = password
        self.driver = webdriver.Firefox()
        self._container = {}
        self.send_account_url = uri_validator(server_url + send_account_url)
        self.send_payment_url = uri_validator(server_url + send_payment_url)
        self.transactions_interval = transactions_interval

    def wait_click_redirect(self, click_item: WebElement) -> None:
        """
        wait clicked element redirect
        """
        current_url = self.driver.current_url
        click_item.click()
        WebDriverWait(self.driver, TIMEOUT).until(EC.url_changes(current_url))

    @abc.abstractmethod
    def auth(self) -> None:
        """
        authenticate in bank client WebGUI
        """

    @abc.abstractmethod
    def account_page_parser(self) -> None:
        """
        parse info about bank account (like Bank Account or Card Bank Account)
        """

    @abc.abstractmethod
    def transaction_page_parser(self) -> None:
        """
        parse page with transactions (payments, receipts and etc.)
        """

    def _send_request(self, url: str, data: Union[Dict, List]) -> None:
        r = requests.post(url=url, json=data)
        if r.status_code != 200:
            print('WARNING: request not sending')

    def send_account_data(self) -> None:
        data = [i.account for i in self._container.keys()]
        self._send_request(url=self.send_account_url, data=data)

    def send_payment_data(self) -> None:
        data = [tr for acc_tr in self._container.values() for tr in acc_tr]
        self._send_request(url=self.send_account_url, data=data)