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


class FazendaSPSpider(scrapy.Spider):
    name = 'fazendaSP'
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

        self.driver.get("https://duc.prefeitura.sp.gov.br/certidoes/forms_anonimo/frmConsultaEmissaoCertificado.aspx")
        print(self.driver.current_url)
        time.sleep(3)

        self.driver.execute_script("document.getElementById('ctl00_ConteudoPrincipal_ddlTipoCertidao').value = 1")
        self.driver.execute_script(
            "document.getElementById('ctl00_ConteudoPrincipal_ddlTipoCertidao').dispatchEvent(new Event('change'))")
        time.sleep(1.5)

        self.type = "CNPJ"
        if len(informations["certificationRequest"]["document"]) == 11:
            print(modifyCPF(informations["certificationRequest"]["document"]))
            self.driver.execute_script("document.getElementById('ctl00_ConteudoPrincipal_ddlTipoDocumento').value = 'CPF'")
            self.driver.execute_script("document.getElementById('ctl00_ConteudoPrincipal_ddlTipoDocumento').dispatchEvent(new Event('change'))")
            time.sleep(1)

            self.driver.execute_script("document.getElementById('ctl00_ConteudoPrincipal_txtCPF').value = '" + modifyCPF(informations["certificationRequest"]["document"]) + "'")
        else:
            print(modifyCNPJ(informations["certificationRequest"]["document"], "COMPLETED"))
            self.driver.execute_script("document.getElementById('ctl00_ConteudoPrincipal_txtCNPJ').value = '" + modifyCNPJ(informations["certificationRequest"]["document"], "COMPLETED") + "'")

        # self.driver.execute_script(
            #"document.getElementById('ctl00_ConteudoPrincipal_txtCNPJ').value = '25.111.602/0001-47'")
        time.sleep(5)

        content = self.driver.find_element_by_id('ctl00_ConteudoPrincipal_imgCaptcha')
        content.screenshot('captcha.png')

        solver = CaptchaSolver('2captcha', api_key=self.settings.get("CLIENT_KEY_2_CAPTCHA"))
        raw_data = open('captcha.png', 'rb').read()
        result = solver.solve_captcha(raw_data)

        os.remove('captcha.png')

        self.driver.find_element_by_id("ctl00_ConteudoPrincipal_txtValorCaptcha").send_keys(result)
        self.driver.find_element_by_id("ctl00_ConteudoPrincipal_btnEmitir").click()
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
            content = None

        else:
            filePath = self.downloadPath + "/" + filenames[0]

            #content = tika_parser(filePath,'')
            content = None

            #os.remove(filePath)

        name = informations["certificationRequest"]["document"] + "_" + datetime.date.today().strftime(
            "%d_%m_%Y") + ".pdf"

        fileName = f'Certidoes/Fazenda SP/{informations["certificationRequest"]["document"]}/CTM_{name}'

        s3_client().upload_file(filePath, self.bucketName, fileName)
        print(filePath)

        os.remove(filePath)

        post_data = {
            "certificationId": informations["id"],
            "path": fileName,
            "content": content
        }

        response = requests.post(self.env + "/v1/certification/upload",
                                 headers={
                                     "x-api-key": "258a0b3c88dbf701892b713a91b793d5",
                                     "x-user": "marcussouza@id.uff.br",
                                     "Content-Type": "application/json",
                                 },
                                 data=json.dumps(post_data))
