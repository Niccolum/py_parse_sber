FROM python:3.7

RUN apt update && apt install -y python3 curl
RUN pip3 install --no-cache-dir py-parser-sber -U
RUN pip3 freeze | grep py-parser-sber

WORKDIR /opt/app

# install firefox
RUN apt-get install -y firefox-esr

# install geckodriver
RUN export geckodriver_ver=$(curl https://github.com/mozilla/geckodriver/releases/latest/ | sed -ne 's/.*tag\/v\(.*\)">.*/\1/p') \
 && echo "geckodriver v${geckodriver_ver}" \
 && curl -fL -o /tmp/geckodriver.tar.gz \
    https://github.com/mozilla/geckodriver/releases/download/v${geckodriver_ver}/geckodriver-v${geckodriver_ver}-linux64.tar.gz \
 && tar -xzf /tmp/geckodriver.tar.gz -C /tmp/ \
 && chmod +x /tmp/geckodriver \
 && mv /tmp/geckodriver /usr/local/bin/

CMD ["py_parser_sber_run_infinite"]