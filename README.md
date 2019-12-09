# Py_parse_sber

## Overview

It's simple parser of Sberbank, using selenium (firefox geckodriver), where you can see your account currency
and  transactions for some period.

## Getting Started
### Requirements

Python 3.6+

### Install

The quick way:
```bash
pip install py_parse_sber
```

Desired way:
```bash
python3 -m venv venv
source venv/bin/activate
pip install py_parse_sber
```

### Using:

Requirement environment variables:
```bash
LOGIN  # your sberbank account login
PASSWORD # your sberbank account password
SERVER_URL # main URL where the data will be sent. Example: http://localhost:8080
SEND_ACCOUNT_URL # url 'path' part, where account information will be sent. Example: /send_account
SEND_PAYMENT_URL # url 'path' part, where transaction information will be sent. Example: /send_payment
```
Optional environment variables:
```bash
DAYS # period in days to indicate parser restart. Can be used with HOURS.
HOURS # period in hours to indicate parser restart. Can be used with DAYS.
```
If any of their not set - used one day by default

## Authors

*   **Nikolai Vidov** - *maintainer* - [Niccolum](https://github.com/Niccolum)

## License

This project is licensed under the MIT License - see the [LICENSE.md](https://github.com/Niccolum/intrst_algrms/blob/master/LICENSE.md) file for details
