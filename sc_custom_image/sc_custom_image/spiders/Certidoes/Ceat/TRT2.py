import datetime
import json
import os
import time

import requests
import scrapy
from PIL import Image
from captcha_solver import CaptchaSolver
from scrapy.utils.project import get_project_settings
from selenium import webdriver

#from sc_custom_image.spiders.common.Extractor import tika_parser
from sc_custom_image.spiders.common.aws_util import s3_client
from sc_custom_image.spiders.common.util import getDownLoadedFileName, modifyCNPJ, modifyCPF


class Trt2SPSpider(scrapy.Spider):
    name = 'trt2'
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

        self.driver.get("https://aplicacoes10.trt2.jus.br/certidao_trabalhista_eletronica/public/index.php/index/solicitacao")
        print(self.driver.current_url)
        time.sleep(3)

        time.sleep(1.5)

        self.driver.fullscreen_window()

        self.type = "CNPJ"
        if len(informations["certificationRequest"]["document"]) == 11:
            print(modifyCPF(informations["certificationRequest"]["document"]))
            self.driver.execute_script("document.getElementById('numeroDocumentoPesquisado').value = '" + modifyCPF(informations["certificationRequest"]["document"]) + "'")
        else:
            print(modifyCNPJ(informations["certificationRequest"]["document"], "COMPLETED"))
            self.driver.find_element_by_id("tipoDocumentoPesquisado-2").click()
            self.driver.execute_script(
                "document.getElementById('tipoDocumentoPesquisado-2').dispatchEvent(new Event('change'))")
            self.driver.execute_script("document.getElementById('numeroDocumentoPesquisado').value = '" + modifyCNPJ(informations["certificationRequest"]["document"], "COMPLETED") + "'")

        time.sleep(5)

        self.driver.find_element_by_id("nomePesquisado").send_keys(informations["certificationRequest"]["fullName"])

        content = self.driver.find_elements_by_tag_name('img')[1]
        content.screenshot('captcha.png')

        solver = CaptchaSolver('2captcha', api_key=self.settings.get("CLIENT_KEY_2_CAPTCHA"))
        raw_data = open('captcha.png', 'rb').read()
        result = solver.solve_captcha(raw_data)

        os.remove('captcha.png')

        self.driver.find_element_by_id("captcha-input").send_keys(result)
        self.driver.find_element_by_id("submit").click()
        time.sleep(3)

        self.driver.find_elements_by_tag_name('button')[3].click()
        time.sleep(3)

        filenames = next(os.walk(self.downloadPath), (None, None, []))[2]
        print(filenames)

        if len(filenames) == 0:
            self.driver.switch_to.window(self.driver.window_handles[0])
            filePath = self.downloadPath + "/Certidao Aux.png"

            self.driver.save_screenshot(filePath)

            image1 = Image.open(filePath)
            im1 = image1.convert('RGB')
            filePath = self.downloadPath + "/Certidao Aux.pdf"
            im1.save(filePath)

            os.remove(self.downloadPath + "/Certidao Aux.png")
        else:
            filePath = self.downloadPath + "/" + filenames[0]

        name = informations["certificationRequest"]["document"] + "_" + datetime.date.today().strftime(
            "%d_%m_%Y") + ".pdf"

        fileName = f'Certidoes/TRT2/{informations["certificationRequest"]["document"]}/{name}'

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
