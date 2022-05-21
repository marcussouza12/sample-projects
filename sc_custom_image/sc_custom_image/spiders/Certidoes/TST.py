import datetime
import json
import os
import time

import requests
import scrapy
from captcha_solver import CaptchaSolver
from scrapy.utils.project import get_project_settings
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait

from selenium.webdriver.support import expected_conditions as EC

# from sc_custom_image.spiders.common.Extractor import tika_parser
from sc_custom_image.spiders.common.aws_util import s3_client
from sc_custom_image.spiders.common.util import modifyCNPJ, modifyCPF


class TSTSpider(scrapy.Spider):
    name = 'tst'
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

        self.driver.get("https://cndt-certidao.tst.jus.br/inicio.faces")
        print(self.driver.current_url)
        time.sleep(3)

        myElem = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '#corpo > div > div:nth-child(2) > input:nth-child(1)')))

        self.driver.execute_script(
            "document.querySelector('#corpo > div > div:nth-child(2) > input:nth-child(1)').click()")
        time.sleep(4)

        document = modifyCPF(informations["certificationRequest"]["document"])
        if informations["certificationRequest"]["documentType"] == "CNPJ":
            document = modifyCNPJ(informations["certificationRequest"]["document"], "COMPLETED")

        self.driver.execute_script(f"document.getElementById('gerarCertidaoForm:cpfCnpj').value = '{document}'")

        '''api_key = os.getenv('APIKEY_2CAPTCHA', self.settings.get("CLIENT_KEY_2_CAPTCHA"))

        solver = TwoCaptcha(api_key)

        result = solver.hcaptcha(
            sitekey='0558d903-532a-43b7-a8fa-3ef6db3cac63',
            url="https://cndt-certidao.tst.jus.br/",
        )

        print(result)

        self.driver.execute_script("document.getElementsByName('h-captcha-response')[0].value = '" + result["code"] + "'")
        #self.driver.execute_script("document.getElementsByName('g-recaptcha-response')[0].value = '" + result["code"] + "'")'''

        content = self.driver.find_element_by_id('idImgBase64')
        content.screenshot('captcha.png')

        solver = CaptchaSolver('2captcha', api_key=self.settings.get("CLIENT_KEY_2_CAPTCHA"))
        raw_data = open('captcha.png', 'rb').read()
        result = solver.solve_captcha(raw_data)

        self.driver.find_element_by_id("idCaptcha").send_keys(result)

        self.driver.execute_script("document.getElementById('gerarCertidaoForm:btnEmitirCertidao').click()")
        time.sleep(10)

        filePath = self.downloadPath + f'/certidao_{informations["certificationRequest"]["document"]}.pdf'
        while not os.path.exists(filePath):
            time.sleep(1)
        if os.path.isfile(filePath):
            print("File Downloaded successfully..")

        name = informations["certificationRequest"]["document"] + "_" + datetime.date.today().strftime(
            "%d_%m_%Y") + ".pdf"
        fileName = f'Certidoes/TST/{informations["certificationRequest"]["document"]}/{name}'

        s3_client().upload_file(filePath, self.bucketName, fileName)
        print(filePath)
        # print(tika_parser(filePath,''))

        post_data = {
            "certificationId": informations["id"],
            "path": fileName,
            # "content": tika_parser(filePath,'')
        }

        os.remove(filePath)

        print(post_data)
        response = requests.post(self.env + "/v1/certification/upload",
                                 headers={
                                     "x-api-key": "258a0b3c88dbf701892b713a91b793d5",
                                     "x-user": "marcussouza@id.uff.br",
                                     "Content-Type": "application/json",
                                 },
                                 data=json.dumps(post_data))

        print(response.status_code)
