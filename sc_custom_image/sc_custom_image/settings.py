# -*- coding: utf-8 -*-

# Scrapy settings for sc_custom_image project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     http://doc.scrapy.org/en/latest/topics/settings.html
#     http://scrapy.readthedocs.org/en/latest/topics/downloader-middleware.html
#     http://scrapy.readthedocs.org/en/latest/topics/spider-middleware.html

BOT_NAME = 'sc_custom_image'

SPIDER_MODULES = ['sc_custom_image.spiders']
NEWSPIDER_MODULE = 'sc_custom_image.spiders'


# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = 'sc_custom_image (+http://www.yourdomain.com)'

# Obey robots.txt rules
ROBOTSTXT_OBEY = True

# Configure maximum concurrent requests performed by Scrapy (default: 16)
#CONCURRENT_REQUESTS = 32

# Configure a delay for requests for the same website (default: 0)
# See http://scrapy.readthedocs.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
#DOWNLOAD_DELAY = 3
# The download delay setting will honor only one of:
#CONCURRENT_REQUESTS_PER_DOMAIN = 16
#CONCURRENT_REQUESTS_PER_IP = 16

# Disable cookies (enabled by default)
#COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
#TELNETCONSOLE_ENABLED = False

# Override the default request headers:
#DEFAULT_REQUEST_HEADERS = {
#   'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
#   'Accept-Language': 'en',
#}

# Enable or disable spider middlewares
# See http://scrapy.readthedocs.org/en/latest/topics/spider-middleware.html
#SPIDER_MIDDLEWARES = {
#    'sc_custom_image.middlewares.MyCustomSpiderMiddleware': 543,
#}

# Enable or disable downloader middlewares
# See http://scrapy.readthedocs.org/en/latest/topics/downloader-middleware.html
#DOWNLOADER_MIDDLEWARES = {
#    'sc_custom_image.middlewares.MyCustomDownloaderMiddleware': 543,
#}

# Enable or disable extensions
# See http://scrapy.readthedocs.org/en/latest/topics/extensions.html
#EXTENSIONS = {
#    'scrapy.extensions.telnet.TelnetConsole': None,
#}

# Configure item pipelines
# See http://scrapy.readthedocs.org/en/latest/topics/item-pipeline.html
#ITEM_PIPELINES = {
#    'sc_custom_image.pipelines.SomePipeline': 300,
#}

# Enable and configure the AutoThrottle extension (disabled by default)
# See http://doc.scrapy.org/en/latest/topics/autothrottle.html
#AUTOTHROTTLE_ENABLED = True
# The initial download delay
#AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
#AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
#AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
#AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See http://scrapy.readthedocs.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
#HTTPCACHE_ENABLED = True
#HTTPCACHE_EXPIRATION_SECS = 0
#HTTPCACHE_DIR = 'httpcache'
#HTTPCACHE_IGNORE_HTTP_CODES = []
#HTTPCACHE_STORAGE = 'scrapy.extensions.httpcache.FilesystemCacheStorage'

# CHROME_PATH = '../chromedriver'
CHROME_PATH = '/Users/marcussouza/Downloads/chromedriver'
# CHROME_PATH = '/path/to/chromedriver'
# CHROME_PATH = '/usr/bin/chromedriver'
FIREFOX_PATH = '/Users/marcussouza/Downloads/geckodriver'

# ENV = 'http://localhost:8080'
ENV = 'https://certification.audiflix.io'

CLIENT_KEY_API_MONSTER = "a4cee99b586218e3908effc7338665dd"
CLIENT_KEY_2_CAPTCHA = "4ae6200073787cd534614f7fc4fb645c"
CLIENT_KEY_CAPTCHAS_IO = "0186db8a-61f3f83b0f1fd4.43701621"

CERTIFICATION_BUCKET = "inove4u-upload-do"

AWS_SECRET_KEY = "VNBcu2vJvQ4xzwKWIxGN/oZGv7cGsst+8b250k4I"
AWS_ACCESS_KEY = "AKIA265227RWQGSHSRRT"
AWS_REGION = "us-east-2"

LOG_LEVEL = 'ERROR'  # to only display errors
LOG_FORMAT = '%(levelname)s: %(message)s'

HEADER_PROCESS_API = {
    "x-api-key": "0381c1d624ff5a06dc4ff63aaa14ab11",
    "x-user": "marcussouza@id.uff.br"
}