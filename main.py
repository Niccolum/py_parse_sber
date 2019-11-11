import os

from sberbank_parse import SberbankClientParser

def main():
    need_env_vars = ['LOGIN', 'PASSWORD', 'SERVER_URL', 
                     'SEND_ACCOUNT_URL', 'SEND_PAYMENT_URL', 'TRANSCTIONS_INTERVAL']
    need_data_for_start = {k.lower(): os.environ[k] for k in need_env_vars}

    sber = SberbankClientParser(**need_data_for_start)
    sber.auth()
    sber.account_page_parser()
    sber.transaction_page_parser()
    print(sber._container)

if __name__ == '__main__':
    main()