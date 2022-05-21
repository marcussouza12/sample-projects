FROM scrapinghub/scrapinghub-stack-scrapy:1.3
RUN apt-get install unzip
RUN printf "deb http://archive.debian.org/debian/ jessie main\ndeb-src http://archive.debian.org/debian/ jessie main\ndeb http://security.debian.org jessie/updates main\ndeb-src http://security.debian.org jessie/updates main" > /etc/apt/sources.list

#============================================
# Firefox and Geckodriver
#============================================
RUN apt-get update                             \
 && apt-get install -y --force-yes --no-install-recommends \
    ca-certificates curl firefox-esr           \
 && rm -fr /var/lib/apt/lists/*                \
 && curl -L https://github.com/mozilla/geckodriver/releases/download/v0.24.0/geckodriver-v0.24.0-linux64.tar.gz | tar xz -C /usr/local/bin \
 && apt-get purge -y --force-yes ca-certificates curl

RUN python -m pip install --upgrade pip

ENV TERM xterm
ENV SCRAPY_SETTINGS_MODULE sc_custom_image.settings
RUN mkdir -p /app
WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY ./ ./
RUN python setup.py install