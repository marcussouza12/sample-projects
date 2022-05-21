import datetime
import json
import os
import pkgutil
import sys
import time
import traceback

import requests
import scrapy
from PIL import Image
from scrapy.utils.project import get_project_settings
from selenium import webdriver

from captcha_solver import CaptchaSolver
from selenium.webdriver.common.proxy import ProxyType, Proxy
from twocaptcha import TwoCaptcha

from sc_custom_image.spiders.common.aws_util import s3_client
from sc_custom_image.spiders.common.util import getDownLoadedFileName, modifyCPF


class TSTSpider(scrapy.Spider):
    name = 'rf'
    start_urls = ['http://quotes.toscrape.com/js']

    def __init__(self, id=''):
        self.settings = get_project_settings()
        self.chromePath = self.settings.get("CHROME_PATH")
        self.bucketName = self.settings.get("CERTIFICATION_BUCKET")

        self.ROOT_DIR = os.path.abspath(os.curdir)
        self.downloadPath = self.ROOT_DIR
        print(self.downloadPath)
        # os.makedirs(downloadPath)

        options = webdriver.ChromeOptions()
        # options.add_argument("--disable-extensions")
        # options.add_argument("--headless")
        # options.add_argument("--disable-gpu")
        # options.add_argument("--no-sandbox")
        options.add_argument(
            "user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36 ")
        options.add_experimental_option("prefs", {
            "download.default_directory": self.downloadPath,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing_for_trusted_sources_enabled": False,
            "safebrowsing.enabled": False
        })

        '''prox = Proxy()
        prox.proxy_type = ProxyType.MANUAL
        prox.http_proxy = "marcussouza:ncPmzbga@160.116.130.229:55393"
        prox.socks_proxy = "marcussouza:ncPmzbga@160.116.130.229:55393"
        prox.ssl_proxy = "marcussouza:ncPmzbga@160.116.130.229:55393"

        capabilities = webdriver.DesiredCapabilities.CHROME
        prox.add_to_capabilities(capabilities)

        options.set_capability(capabilities)'''

        # options.add_argument('--proxy-server=160.116.130.229:55393')

        self.driver = webdriver.Chrome(chrome_options=options, executable_path=self.chromePath)
        params = {'behavior': 'allow', 'downloadPath': self.downloadPath}
        self.driver.execute_cdp_cmd("Page.setDownloadBehavior", params)

        self.id = id

        self.settings = get_project_settings()
        self.env = self.settings.get("ENV")

    def parse(self, response):
        response = requests.get(self.env + "/v1/certification/" + self.id,
                                headers={
                                    "x-api-key": "258a0b3c88dbf701892b713a91b793d5",
                                    "x-user": "marcussouza@id.uff.br"
                                })

        informations = json.loads(response.content)

        print(informations)

        site = "PF"
        if informations["certificationRequest"]["documentType"] == 'CNPJ':
            site = 'PJ'
        else:
            self.searchCPF(self.driver, informations)

    def searchCPF(self, driver, informations):
        settings = get_project_settings()
        driver.get("https://servicos.receita.fazenda.gov.br/Servicos/CPF/ConsultaSituacao/ConsultaPublica.asp")
        print(driver.current_url)
        time.sleep(3)

        config = {
            "captchaInfo": {"captcha_service": "CLIENT_KEY_2_CAPTCHA"}
        }

        captchas = {
            "CLIENT_KEY_CAPTCHAS_IO": {
                "urlIn": "https://api.captchas.io/in.php",
                "urlRes": "https://api.captchas.io/res.php"
            },

            "CLIENT_KEY_2_CAPTCHA": {
                "urlIn": "https://2captcha.com/in.php",
                "urlRes": "https://2captcha.com/res.php"
            },

            "CLIENT_KEY_API_MONSTER": {
                "urlIn": "",
                "urlRes": ""
            }
        }["CLIENT_KEY_2_CAPTCHA"]

        api_key = os.getenv('APIKEY_2CAPTCHA', settings.get("CLIENT_KEY_2_CAPTCHA"))

        solver = TwoCaptcha(api_key)

        try:
            result = solver.hcaptcha(
                sitekey='af4fc5a3-1ac5-4e6d-819d-324d412a5e9d',
                url=driver.current_url,
                invisible=0
            )

        except Exception as e:
            sys.exit(e)

        else:
            # sys.exit('solved: ' + str(result))
            print(result["code"])

            driver.execute_script(
                "document.getElementsByName('h-captcha-response')[0].value = '" + result["code"] + "'")

        driver.execute_script("document.getElementById('txtCPF').value = '" + modifyCPF(
            informations["certificationRequest"]["document"]) + "'")
        driver.execute_script("document.getElementById('txtCPF').dispatchEvent(new Event('change'))")
        time.sleep(1)

        driver.execute_script(
            "document.getElementById('txtDataNascimento').value = '" + informations["certificationRequest"][
                "birthday"] + "'")
        driver.execute_script("document.getElementById('txtDataNascimento').dispatchEvent(new Event('change'))")
        time.sleep(1)

        driver.find_element_by_id("id_submit").click()
        time.sleep(2)
