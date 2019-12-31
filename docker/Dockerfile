FROM python:3.7

RUN apt update && apt install -y python3 curl
RUN pip3 install --no-cache-dir py-parser-sber

WORKDIR /opt/app

CMD ["py_parser_sber_run_infinite"]