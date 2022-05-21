import base64
import datetime
import json
import os
import time
from PIL import Image

import requests
import scrapy
from scrapy.utils.project import get_project_settings
from selenium import webdriver

#from sc_custom_image.spiders.common.Extractor import tika_parser
from selenium.webdriver.common.by import By

from sc_custom_image.spiders.common.aws_util import s3_client
from sc_custom_image.spiders.common.util import modifyCNPJ, modifyCPF


class ProtestosSPSpider(scrapy.Spider):
    name = 'protestosSP'
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

        self.driver.get("http://protestosp.com.br/consulta-de-protesto")
        print(self.driver.current_url)
        time.sleep(3)

        #self.driver.find_element_by_css_selector('#cf-root > div > div > div > div.cf2L3T.cfysV4.cf3l36 > div.cf3Tgk.cf1IKf > div:nth-child(2) > button').click()
        #time.sleep(0.5)

        self.driver.execute_script("document.getElementById('AbrangenciaNacional').click()")
        self.driver.execute_script("document.getElementById('AbrangenciaNacional').dispatchEvent(new Event('change'))")
        time.sleep(1.5)

        self.type = "CNPJ"
        if len(informations["certificationRequest"]["document"]) == 11:
            document = modifyCPF(informations["certificationRequest"]["document"])
            self.driver.execute_script("document.getElementById('TipoDocumento').value = 1")
        else:
            document = modifyCNPJ(informations["certificationRequest"]["document"], "COMPLETED")
            self.driver.execute_script("document.getElementById('TipoDocumento').value = 2")

        self.driver.execute_script("document.getElementById('TipoDocumento').dispatchEvent(new Event('change'))")

        self.driver.execute_script("document.getElementById('Documento').value = '" + document + "'")
        self.driver.execute_script("document.getElementById('Documento').dispatchEvent(new Event('change'))")

        #self.driver.save_screenshot("load.png")

        self.driver.execute_script("document.querySelector('#frmConsulta > input.btn-padrao.blue.borderEffect2.mt-3.hoverEffect.wider3').click()")
        time.sleep(8)

        print(self.driver.find_element(by=By.ID, value="btnfecharMessage") is not None)
        if self.driver.find_element(by=By.ID, value="btnfecharMessage") is not None:
            self.driver.find_element(by=By.ID, value="btnfecharMessage").click()

        filePNG = self.downloadPath + "/Certidao Aux.png"

        S = lambda X: self.driver.execute_script('return document.body.parentNode.scroll'+X)
        self.driver.set_window_size(S('Width'),S('Height')) # May need manual adjustment
        self.driver.find_element_by_tag_name('body').screenshot(filePNG)

        #self.driver.save_screenshot(filePNG)

        image1 = Image.open(filePNG)
        im1 = image1.convert('RGB')

        filePath = self.downloadPath + "/Certidao Aux.pdf"
        im1.save(filePath)

        os.remove(filePNG)

        name = informations["certificationRequest"]["document"] + "_" + datetime.date.today().strftime("%d_%m_%Y") + ".pdf"
        fileName = f'Certidoes/Protestos SP/{informations["certificationRequest"]["document"]}/{name}'

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
