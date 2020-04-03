# Py_parse_sber

## Overview

It's simple parser of Sberbank, using selenium (firefox geckodriver), where you can see your account currency
and transactions for some period.

## Getting Started

**For the program to work, you must disable two-factor authorization on the sberbank-online website, 
otherwise the program will not work**

### Requirements

Python 3.6+

### Install

The quick way:
```bash
pip install py-parse-sber
```

Desired way:
```bash
python3 -m venv venv
source venv/bin/activate
pip install py-parse-sber
```

### Preparing:

#### Install geckodriver

Download [geckodriver](https://github.com/mozilla/geckodriver/releases) and unzip it
Make sure it’s in your PATH, e. g., place it in /usr/bin or /usr/local/bin.

Failure to observe this step will give you an error selenium.common.exceptions.WebDriverException: 
Message: ‘geckodriver’ executable needs to be in PATH.

#### Run receiving web server

Py_parse_sber will send parsed info to web server.
See contracts detail in [contracts.yml](https://github.com/Niccolum/py_parse_sber/blob/master/contracts.yml),
which your web server will have to implement for accepting data correct. 
(for standard was taken project [BudgetTracker](https://github.com/DiverOfDark/BudgetTracker) and his 
[api](https://github.com/DiverOfDark/BudgetTracker#%D0%B8%D1%81%D1%82%D0%BE%D1%87%D0%BD%D0%B8%D0%BA%D0%B8-%D0%B4%D0%B0%D0%BD%D0%BD%D1%8B%D1%85))

#### Requirement environment variables

```bash
LOGIN  # your sberbank account login
PASSWORD # your sberbank account password
SERVER_URL # main URL where the data will be sent. Example: localhost (or service name in docker-compose.yml)
SEND_ACCOUNT_URL # url 'path' part, where account information will be sent. Example: /send_account
SEND_PAYMENT_URL # url 'path' part, where transaction information will be sent. Example: /send_payment
```

#### Optional environment variables
```bash
SERVER_SCHEME # Scheme of SERVER_URL, http/https. Default http
SERVER_PORT # Port of SERVER_URL. Default 80
DAYS # period in days to indicate parser restart. Can be used with HOURS.
HOURS # period in hours to indicate parser restart. Can be used with DAYS.
```
If any of their not set - used 1 day by default.

## Linux example
```bash
export LOGIN=login
export PASSWORD=password
export SERVER_URL=localhost
export SERVER_PORT=8080
export SEND_ACCOUNT_URL=/send_account
export SEND_PAYMENT_URL=/send_payment

py_parser_sber_run_once # for one-time launch
# or
py_parser_sber_run_infinite # for run in loop with a given period
```

## Docker-compose example
```bash
$ cat .env
```
```.env
LOGIN=<login>
PASSWORD=<password>
SERVER_URL=example.com
SERVER_SCHEME=https
SERVER_PORT=80
SEND_ACCOUNT_URL=/send_account
SEND_PAYMENT_URL=/send_payment
DAYS=1
```

```bash
$ cat docker-compose.yml
```
```yaml
version: '3.4'

services:
  py_parse_sber:
    image: niccolum/py_parse_sber/py_parse_sber:latest
    env_file:
      - .env
    volumes:
      - ./:/opt/app
```

Also see dev example [docker-compose.yml](https://github.com/Niccolum/py_parse_sber/blob/master/docker-compose.yml)

## Authors

*   **Nikolai Vidov** - *maintainer* - [Niccolum](https://github.com/Niccolum)

## License

This project is licensed under the MIT License - see the [LICENSE.md](https://github.com/Niccolum/py_parse_sber/blob/master/LICENSE.md) file for details
