from typing import Optional, Iterator, Type, Dict
import uuid
import datetime
from contextlib import suppress
import logging

from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from py_parser_sber.abstract import (
    AbstractSberbankAccount,
    AbstractProcessedTransaction,
    Transaction,
    AbstractClientParser,
    TIMEOUT)
from py_parser_sber.utils import (
    check_authorization,
    sber_time_format,
    replace_formatter,
    currency_converter)


logger = logging.getLogger(__name__)

class BankAccountAbstract(AbstractSberbankAccount):
    acc_type = 'account'


class CardAccountAbstract(AbstractSberbankAccount):
    acc_type = 'card'


class SberbankProcessedTransaction(AbstractProcessedTransaction):

    @property
    def transaction_id(self) -> str:
        return uuid.uuid5(uuid.NAMESPACE_X500, repr(self)).hex

    @property
    def transaction(self) -> Transaction:
        return Transaction(id=self.transaction_id, transaction=self)

    @classmethod
    def transaction_parser(
            cls, driver: WebDriver, account: AbstractSberbankAccount
    ) -> Iterator[Optional['SberbankProcessedTransaction']]:

        transactions_table = driver.find_element(By.ID, 'simpleTable0')

        with suppress(NoSuchElementException):
            driver.find_element(By.XPATH, "//div[contains(@class, 'emptyText')]")
            return

        if driver.find_element(By.ID, 'pagination').is_displayed():
            driver.find_elements(By.XPATH, "//span[contains(@class, 'paginationSize')]")[-1].click()
            transactions_table = driver.find_element(By.ID, 'simpleTable0')

        while True:
            curr_day_transactions = []
            prev_transaction_data = cls.transaction_time_parse('Сегодня')
            print('current date:', prev_transaction_data)

            for transaction_el in transactions_table.find_elements(By.XPATH, ".//tr[contains(@class, 'ListLine')]"):
                raw_info = [i.text for i in transaction_el.find_elements(By.XPATH, "./td")]
                curr_transaction_date = cls.transaction_time_parse(raw_info[3])
                raw_cost, raw_currency = raw_info[4].rsplit(' ', 1)

                raw_transaction = {
                    'account_name': account.name,
                    'time': curr_transaction_date,
                    'cost': replace_formatter(raw_cost, delete_symbols=' ', custom={',': '.'}),
                    'currency': currency_converter(raw_currency),
                    'description': raw_info[0].rsplit('\n', 1)[0],
                }

                if prev_transaction_data == curr_transaction_date:
                    print('add to curr_day')
                    print(raw_transaction)
                    curr_day_transactions.append(raw_transaction)
                else:
                    yield from cls.add_custom_unique_tr_id(curr_day_transactions)
                    curr_day_transactions.clear()
                    prev_transaction_data = curr_transaction_date
                    curr_day_transactions.append(raw_transaction)

            paginator = transactions_table.find_element(By.ID, 'pagination')
            if paginator.is_displayed():
                paginator_next = paginator.find_elements(By.XPATH, ".//table[contains(@class, 'tblPagin')]//td")[2]

                with suppress(NoSuchElementException):
                    button = paginator_next.find_element(By.XPATH, ".//div[contains(@class, 'activePaginRightArrow')]")

                    if button.get_attribute('class').startswith('inactive'):
                        yield from cls.add_custom_unique_tr_id(curr_day_transactions)
                        break

                    button.click()
                    transactions_table = WebDriverWait(driver, TIMEOUT).until(
                        EC.presence_of_element_located((By.ID, 'simpleTable0')))
            else:
                yield from cls.add_custom_unique_tr_id(curr_day_transactions)
                break

    @classmethod
    def add_custom_unique_tr_id(cls, raw_tr_list: Iterator[Dict[str, str]]) -> Transaction:
        print('return current day transactions')
        for order_id, curr_day_raw_tr in enumerate(reversed(raw_tr_list), 1):
            curr_day_raw_tr['order_id'] = order_id

        for raw_tr in raw_tr_list:
            yield cls(**raw_tr).transaction

    @staticmethod
    def transaction_time_parse(raw_time: str) -> str:
        if raw_time == 'Сегодня':
            time = datetime.date.today()
        elif raw_time == 'Вчера':
            time = datetime.date.today() - datetime.timedelta(days=1)
        else:
            try:
                raw_time_tuple = tuple(map(int, raw_time.split('.')))
            except Exception as err:
                print('WARNING, incorrect time:\n{err}\n{raw_time}'.format(err=err, raw_time=raw_time))
                return raw_time
            else:
                headers = ['day', 'month', 'year']
                dict_time = dict(zip(headers, raw_time_tuple))
                curr_year = datetime.date.today().year
                dict_time.setdefault('year', curr_year)
                time = datetime.date(**dict_time)
        return '{:%Y.%m.%d}'.format(time)


class SberbankClientParser(AbstractClientParser):
    main_page = "https://online.sberbank.ru/"

    def __init__(self, **kwargs):
        self.main_menu_link = None
        super(SberbankClientParser, self).__init__(**kwargs)

    def auth(self) -> None:
        """
        autheticate in sberbank-online
        """
        self.driver.get(self.main_page)

        login_input = self.driver.find_element(By.ID, "loginByLogin")
        login_input.send_keys(self.login)

        password_input = self.driver.find_element(By.ID, "password")
        password_input.send_keys(self.password)

        form = self.driver.find_element(By.ID, "homeAuth")
        form_button = form.find_element(By.XPATH, "button[@type='button']")

        self.wait_click_redirect(form_button)
        self.main_menu_link = self.driver.current_url

    @check_authorization
    def account_page_parser(self, text: str, account: Type[AbstractSberbankAccount]) -> None:
        # go to main page
        self.driver.get(self.main_menu_link)

        # go to page with funds
        link = self.driver.find_element(By.PARTIAL_LINK_TEXT, text)
        self.wait_click_redirect(link)

        # get info about every funds
        raw_accounts = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'productCover')]")
        for raw_account in raw_accounts:
            parsed_account = account.account_parser(raw_account)
            self._container[parsed_account] = []

    def account_page_parser_BankAccount(self) -> None:
        text = 'Все вклады и счета'
        account = BankAccountAbstract
        self.account_page_parser(text=text, account=account)

    def account_page_parser_CardAccount(self) -> None:
        text = 'Все карты'
        account = CardAccountAbstract
        self.account_page_parser(text=text, account=account)

    @check_authorization
    def transaction_page_parser(self, interval: int) -> None:
        # go to main page
        self.driver.get(self.main_menu_link)

        # go to page with transactions history
        text = 'История операций'
        transaction_form_template = ("//ul[contains(@class, 'linksList')]/li/a/div[contains(@class, 'greenTitle')]/"
                          f"span[contains(text(), '{text}')]")
        link = self.driver.find_element(By.XPATH, transaction_form_template)
        self.wait_click_redirect(link)

        for account in self._container.keys():


            # pass data from form to transaction parser
            transaction_iterator = SberbankProcessedTransaction.transaction_parser(self.driver, account)
            for transaction_item in transaction_iterator:
                self._container[account].append(transaction_item.transaction)

    def transaction_form_filter(self, account: Type[AbstractSberbankAccount]):
        # show filter popup if it hidden
        if not self.driver.find_element(By.CLASS_NAME, 'filterMore').is_displayed():
            self.driver.find_element(By.CLASS_NAME, 'extendFilterButton').click()

        # prepare_form
        filter_form = self.driver.find_element(By.CLASS_NAME, 'filterMore')

        # get sberbank account id in format "type:id"
        acc_type = account.acc_type
        acc_id = account.account_id
        acc_value = f'{acc_type}:{acc_id}'

        # choose account for search
        filter_form.find_element(By.ID, 'customSelect1').click()  # create account selection
        sel = filter_form.find_element(By.XPATH, f"//div[@id='customSelect1_List']//li[@value='{acc_value}']")
        sel.click()

        # choose datetime interval
        to_date = datetime.datetime.now()
        from_date = to_date - datetime.timedelta(seconds=interval)

        from_date_field = filter_form.find_element(By.ID, 'filter(fromDate)')
        from_date_field.clear()
        from_date_field.send_keys(sber_time_format(from_date))

        to_date_field = filter_form.find_element(By.ID, 'filter(toDate)')
        to_date_field.clear()
        to_date_field.send_keys(sber_time_format(to_date))

        # get only transactions with money (exclude free reports, for example)
        min_money_field = filter_form.find_element(
            By.XPATH, './/div[@class="amountTitle"]/input[@class="moneyField"]')
        min_money_field.send_keys('0.01')

        # submit form
        text = 'Применить'
        transaction_form_button_xpath = (".//div[contains(@class, 'commandButton')]//"
                                         f"span[contains(text(), '{text}')]")
        filter_form.find_element(By.XPATH, transaction_form_button_xpath).click()

