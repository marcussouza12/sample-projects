import datetime
import fnmatch
import json
import os
import sys
import time
import urllib
from io import BytesIO

import requests
import scrapy
from scrapy.utils.project import get_project_settings
from selenium import webdriver

from twocaptcha import TwoCaptcha

#from sc_custom_image.spiders.common.Extractor import tika_parser
from sc_custom_image.spiders.common.aws_util import s3_client
from sc_custom_image.spiders.common.util import getDownLoadedFileName, modifyCNPJ, modifyCPF


class DividaAtivaSPSpider(scrapy.Spider):
    name = 'dividaAtivaSP'
    start_urls = ['http://quotes.toscrape.com/js']

    def __init__(self, id=''):
        self.settings = get_project_settings()
        self.chromePath = self.settings.get("CHROME_PATH")
        self.bucketName = self.settings.get("CERTIFICATION_BUCKET")

        ROOT_DIR = os.path.abspath(os.curdir)
        self.downloadPath = ROOT_DIR + "/temp"
        print(self.downloadPath)
        # os.makedirs(downloadPath)

        options = webdriver.FirefoxOptions()
        #options.add_argument("--ignore-certificate-erros")
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        #options.add_argument("--incognito")

        settings = get_project_settings()
        self.env = settings.get("ENV")

        HEADLESS_PROXY = "9802902e2fe646869bf82fbe02c4ac93:@proxy.crawlera.com:8011"
        webdriver.DesiredCapabilities.FIREFOX['proxy'] = {
            "httpProxy": HEADLESS_PROXY,
            "sslProxy": HEADLESS_PROXY,
            "proxyType": "MANUAL",
        }

        profile = webdriver.FirefoxProfile()
        profile.set_preference("browser.download.folderList", 2)
        profile.set_preference("browser.download.manager.showWhenStarting", False)
        profile.set_preference("browser.download.dir", self.downloadPath)
        profile.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/pdf")
        profile.set_preference("print.always_print_silent", True)

        profile.set_preference("pdfjs.disabled", True)

        profile.set_preference("plugin.scan.Acrobat", "99.0")
        profile.set_preference("plugin.scan.plid.all", False)

        self.driver = webdriver.Firefox(executable_path=settings.get("FIREFOX_PATH"),
                                        options=options, firefox_profile=profile)

        self.id = id

        settings = get_project_settings()
        self.env = settings.get("ENV")

    def parse(self, response):
        response = requests.get(self.env + "/v1/certification/" + self.id,
                                headers={
                                    "x-api-key": "258a0b3c88dbf701892b713a91b793d5",
                                    "x-user": "marcussouza@id.uff.br"
                                })

        informations = json.loads(response.content)

        print(informations)

        self.driver.get("https://www.dividaativa.pge.sp.gov.br/sc/pages/crda/emitirCrda.jsf")
        print(self.driver.current_url)
        time.sleep(3)

        if informations["certificationRequest"]["documentType"] == "CNPJ":
            document = modifyCNPJ(informations["certificationRequest"]["document"], "COMPLETED").split("/")[0]
            self.driver.execute_script(f"document.getElementById('emitirCrda:crdaInputCnpjBase').value = '{document}'")
        else:
            document = modifyCPF(informations["certificationRequest"]["document"])
            self.driver.execute_script(f"document.getElementById('emitirCrda:crdaInputCpf').value = '{document}'")

        api_key = os.getenv('APIKEY_2CAPTCHA', self.settings.get("CLIENT_KEY_2_CAPTCHA"))

        solver = TwoCaptcha(api_key)

        result = solver.solve_captcha(
            site_key='6Le9EjMUAAAAAPKi-JVCzXgY_ePjRV9FFVLmWKB_',
            page_url="https://www.dividaativa.pge.sp.gov.br/sc/pages/crda/emitirCrda.jsf",
        )

        print(result)

        #self.driver.execute_script("document.getElementsByName('h-captcha-response')[0].value = '" + result["code"] + "'")
        self.driver.execute_script("document.getElementsByName('g-recaptcha-response')[0].value = '" + result + "'")

        self.driver.execute_script("document.getElementsByTagName('input')[7].click()")
        time.sleep(10)

        filenames = next(os.walk(self.downloadPath), (None, None, []))[2]
        print(filenames)
        filePath = self.downloadPath + "/" + filenames[0]

        name = informations["certificationRequest"]["document"] + "_" + datetime.date.today().strftime("%d_%m_%Y") + ".pdf"
        fileName = f'Certidoes/Divida Ativa SP/{informations["certificationRequest"]["document"]}/{name}'

        s3_client().upload_file(filePath, self.bucketName, fileName)
        print(filePath)
        #print(tika_parser(filePath,''))

        post_data = {
            "certificationId": informations["id"],
            "path": fileName,
            #"content": tika_parser(filePath,'')
        }

        os.remove(filePath)

        response = requests.post(self.env + "/v1/certification/upload",
                                 headers={
                                     "x-api-key": "258a0b3c88dbf701892b713a91b793d5",
                                     "x-user": "marcussouza@id.uff.br",
                                     "Content-Type": "application/json",
                                 },
                                 data=json.dumps(post_data))

    def getDownLoadedFileName(self, waitTime):
        self.driver.execute_script("window.open()")
        # switch to new tab
        self.driver.switch_to.window(self.driver.window_handles[-1])
        # navigate to chrome downloads
        self.driver.get('chrome://downloads')
        # define the endTime
        endTime = time.time()+waitTime
        while True:
            try:
                return self.driver.execute_script("return document.querySelector('downloads-manager').shadowRoot.querySelector('#downloadsList downloads-item').shadowRoot.querySelector('div#content  #file-link').text")
            except:
                pass
            time.sleep(1)
            if time.time() > endTime:
                break



