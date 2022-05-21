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

from sc_custom_image.spiders.common.aws_util import s3_client
from sc_custom_image.spiders.common.util import modifyCPF


class FazendaSPSpider(scrapy.Spider):
    name = 'jucesp'
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

        self.driver.get("https://www.jucesponline.sp.gov.br/Login.aspx?ReturnUrl=%2fResultadoBusca.aspx?IDProduto=")
        print(self.driver.current_url)
        time.sleep(3)

        content = self.driver.find_elements_by_css_selector(
            '#formBuscaAvancada > div:nth-child(2) > table > tbody > tr:nth-child(3) > td > div > div:nth-child(1) > img')[
            0]
        content.screenshot('captcha.png')

        solver = CaptchaSolver('2captcha', api_key=self.settings.get("CLIENT_KEY_2_CAPTCHA"))
        raw_data = open('captcha.png', 'rb').read()
        result = solver.solve_captcha(raw_data)

        os.remove('captcha.png')

        self.driver.find_elements_by_name("ctl00$cphContent$CaptchaControl1")[0].send_keys(result)

        self.driver.execute_script("document.getElementById('ctl00_cphContent_txtEmail').value = '129.170.647-06'")
        self.driver.execute_script("document.getElementById('ctl00_cphContent_txtSenha').value = 'Dch&ck001'")
        time.sleep(0.5)

        self.driver.find_element_by_id("ctl00_cphContent_btEntrar").click()
        time.sleep(3)

        self.driver.execute_script("document.getElementById('ctl00_cphContent_frmBuscaSimples_lnkPesquisa_Avancada"
                                   "').click()")
        time.sleep(3)

        self.driver.execute_script("document.getElementById('ctl00_cphContent_frmBuscaAvancada_txtDocumentoSocio"
         "').value = '" + modifyCPF(informations["certificationRequest"]["document"]) + "'")
        #self.driver.execute_script("document.getElementById('ctl00_cphContent_frmBuscaAvancada_txtDocumentoSocio"
                                   #"').value = '391.881.298-70'")

        self.driver.execute_script("document.getElementById('ctl00_cphContent_frmBuscaAvancada_btPesquisar').click()")
        time.sleep(3)

        content = self.driver.find_elements_by_css_selector(
            '#formBuscaAvancada > table > tbody > tr:nth-child(1) > td > div > div:nth-child(1) > img')[0]
        content.screenshot('captcha.png')

        solver = CaptchaSolver('2captcha', api_key=self.settings.get("CLIENT_KEY_2_CAPTCHA"))
        raw_data = open('captcha.png', 'rb').read()
        result = solver.solve_captcha(raw_data)

        os.remove('captcha.png')

        self.driver.find_elements_by_name("ctl00$cphContent$gdvResultadoBusca$CaptchaControl1")[0].send_keys(result)

        print(result)
        self.driver.execute_script("document.getElementById('ctl00_cphContent_gdvResultadoBusca_btEntrar').click()")
        time.sleep(3)

        if len(self.driver.find_elements_by_css_selector(
                '#formBuscaAvancada > table > tbody > tr:nth-child(1) > td > div > div:nth-child(1) > img')) > 1:
            raise "Captcha not broken"

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

        name = informations["certificationRequest"]["document"] + "_" + datetime.date.today().strftime(
            "%d_%m_%Y") + ".pdf"

        fileName = f'Certidoes/JUCESSP/{informations["certificationRequest"]["document"]}/{name}'

        s3_client().upload_file(filePath, self.bucketName, fileName)
        print(filePath)

        post_data = {
            "certificationId": informations["id"],
            "path": fileName
        }

        response = requests.post(self.env + "/v1/certification/docs",
                                 headers={
                                     "x-api-key": "258a0b3c88dbf701892b713a91b793d5",
                                     "x-user": "marcussouza@id.uff.br",
                                     "Content-Type": "application/json",
                                 },
                                 data=json.dumps(post_data))

        print(response.status_code)

        os.remove(filePath)

        company = self.driver.find_elements_by_css_selector(
            '#ctl00_cphContent_gdvResultadoBusca_gdvContent > tbody > tr')

        if len(company) > 1:

            for x in range(1, len(company)):
                company = self.driver.find_elements_by_css_selector(
                    '#ctl00_cphContent_gdvResultadoBusca_gdvContent > tbody > tr')

                columns = company[x].find_elements_by_tag_name('td')

                NIRE = columns[0].text.strip()
                name = columns[1].text
                mun = columns[2].text

                columns[0].click()
                time.sleep(3)

                filePNG = self.downloadPath + "/Certidao Aux.png"

                S = lambda X: self.driver.execute_script('return document.body.parentNode.scroll'+X)
                self.driver.set_window_size(S('Width'), S('Height')) # May need manual adjustment
                self.driver.find_element_by_tag_name('body').screenshot(filePNG)

                image1 = Image.open(filePNG)
                im1 = image1.convert('RGB')
                filePath = self.downloadPath + "/Certidao Aux.pdf"
                im1.save(filePath)

                os.remove(filePNG)

                name = informations["certificationRequest"]["document"] + "_" + datetime.date.today().strftime(
                    "%d_%m_%Y") + f"_{NIRE}_{name}" + ".pdf"

                fileName = f'Certidoes/JUCESSP/{informations["certificationRequest"]["document"]}/{name}'

                s3_client().upload_file(filePath, self.bucketName, fileName)
                print(filePath)

                os.remove(filePath)

                self.driver.back()
                time.sleep(2)

                post_data = {
                    "certificationId": informations["id"],
                    "path": fileName
                }

                response = requests.post(self.env + "/v1/certification/docs",
                                         headers={
                                             "x-api-key": "258a0b3c88dbf701892b713a91b793d5",
                                             "x-user": "marcussouza@id.uff.br",
                                             "Content-Type": "application/json",
                                         },
                                         data=json.dumps(post_data))

                print(response.content)
                print(response.status_code)

        response = requests.put(self.env + "/v1/certification/docs/" + str(informations["id"]),
                                headers={
                                    "x-api-key": "258a0b3c88dbf701892b713a91b793d5",
                                    "x-user": "marcussouza@id.uff.br",
                                    "Content-Type": "application/json",
                                })

        print(response.content)
        print(response.status_code)
        self.driver.close()
