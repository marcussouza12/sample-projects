import datetime
import json
import os
import time

import requests
import scrapy
#import tika
from captcha_solver import CaptchaSolver

from scrapy.utils.project import get_project_settings
from selenium import webdriver

#from sc_custom_image.spiders.common.Extractor import tika_parser
from sc_custom_image.spiders.common.aws_util import s3_client
from sc_custom_image.spiders.common.util import getDownLoadedFileName, modifyCNPJ, modifyCPF
#from tika import parser
import PyPDF2


class Trt3SPSpider(scrapy.Spider):
    name = 'trt3'
    start_urls = ['http://quotes.toscrape.com/js']

    def __init__(self, id='', code='', docType=''):
        # tika.initVM()
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

        self.code = code

        self.type = "CNPJ"
        if len(self.code) == 11 or docType == 'CPF':
            self.type = "CPF"

    def parse(self, response):
        result = []
        if self.id != '':
            response = requests.get(self.env + "/v1/certification/" + self.id,
                                    headers={
                                        "x-api-key": "258a0b3c88dbf701892b713a91b793d5",
                                        "x-user": "marcussouza@id.uff.br"
                                    })

            self.informations = json.loads(response.content)

            print(self.informations)

            info = {
                "code": self.informations["certificationRequest"]["document"],
                "tribunalRadarId": -1,
                "id": -1,
                "uid": -1
            }

            result.append(info)

        else:
            print("aqui")
            self.start_urls = f"http://tartarus2-env.eba-pqv9pzt9.us-east-2.elasticbeanstalk.com/v1/radar/tribunal/TRT3Ceat/{self.type}"
            if self.code != "":
                self.start_urls = self.start_urls + f"?code={self.code}"

            result = json.loads(requests.get(self.start_urls).content)

        for q in result:
            self.driver.get("https://certidao.trt3.jus.br/certidao/feitosTrabalhistas/aba1.emissao.htm")
            print(self.driver.current_url)
            time.sleep(3)
            self.type = "CNPJ"
            tipoPessoa = 'F'
            document = modifyCPF(q["code"])
            if len(q["code"]) == 11:
                self.driver.execute_script("document.getElementById('form:inputCPF').value = '" + document + "'")
                self.driver.execute_script("document.getElementById('form:inputCPF').dispatchEvent(new Event('change'))")

            else:
                tipoPessoa = 'J'
                self.driver.execute_script(
                    "document.getElementsByClassName('ui-radiobutton-box ui-widget ui-corner-all ui-state-default')[1].click()")
                time.sleep(0.5)
                self.driver.find_element_by_id("form:inputCNPJ").send_keys(document)
                self.driver.execute_script("document.getElementById('form:inputCNPJ').dispatchEvent(new Event('change'))")

            #viewState = self.driver.find_element_by_id("javax.faces.ViewState").get_attribute("value")
            #print(viewState)
            #print(self.driver.get_cookies())
            #self.post_name(self.driver.get_cookies(), tipoPessoa, document, viewState)
            time.sleep(3)
            #self.driver.save_screenshot('captcha 4.png')

            content = self.driver.find_elements_by_tag_name('img')[2]
            content.screenshot('captcha.png')

            solver = CaptchaSolver('2captcha', api_key=self.settings.get("CLIENT_KEY_2_CAPTCHA"))
            raw_data = open('captcha.png', 'rb').read()
            result = solver.solve_captcha(raw_data)

            os.remove('captcha.png')

            self.driver.execute_script("document.getElementById('form:verifyCaptcha_').value = '" + result + "'")
            self.driver.execute_script("document.getElementById('form:verifyCaptcha_').dispatchEvent(new Event('change'))")
            #self.driver.find_element_by_id("form:verifyCaptcha_").send_keys(result)

            #self.driver.save_screenshot('captcha 0.png')
            #self.driver.execute_script("PrimeFaces.monitorDownload(startDownload, stopDownload);")
            self.driver.execute_script("document.getElementById('form:botaoConsultar').click()")
            # self.driver.find_element_by_id("form:botaoConsultar").click()
            time.sleep(10)

            #self.driver.save_screenshot('captcha 2.png')

            filenames = next(os.walk(self.downloadPath), (None, None, []))[2]
            #print(filenames)

            #self.driver.save_screenshot('captcha 3.png')

            filePath = self.downloadPath + "/" + filenames[0]

            if self.id != '':
                name = self.informations["certificationRequest"]["document"] + "_" + datetime.date.today().strftime(
                    "%d_%m_%Y") + ".pdf"

                fileName = f'Certidoes/TRT3/{self.informations["certificationRequest"]["document"]}/{name}'

                s3_client().upload_file(filePath, self.bucketName, fileName)
                print(filePath)
                #print(tika_parser(filePath,''))

                post_data = {
                    "certificationId": self.informations["id"],
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

            else:
                #filePath = self.downloadPath + "/CEAT-trt3-33061813011770.pdf"
                '''raw = parser.from_file(filePath)

                text = raw['content'].replace("(PJe)", " ").replace(".", "").replace("-", "").replace("\n", " ").split(" ")
                processes = []
                for word in text:
                    #print(word)
                    if len(word) == 20:
                        if "503" in word:
                            processes.append(word)'''

                # creating a pdf file object
                pdfFileObj = open(filePath, 'rb')

                # creating a pdf reader object
                pdfReader = PyPDF2.PdfFileReader(pdfFileObj)

                # printing number of pages in pdf file
                print(pdfReader.numPages)
                processes = []
                for page in range(0, pdfReader.numPages):
                    pageObj = pdfReader.getPage(page)

                    # extracting text from page
                    text = pageObj.extractText().replace("(PJe)", " ").replace(".", "").replace("-", "").replace("\n", " ").split(" ")
                    for word in text:
                        #print(word)
                        if len(word) == 20:
                            if "503" in word:
                                processes.append(word)

                # closing the pdf file object
                pdfFileObj.close()

                #print(q)
                resp = {
                    "radarId": q["id"],
                    "processes": processes,
                    "court": "TRT3Ceat",
                    "uid": q["uid"],
                    "userLogged": "ANONYMOUS",
                    "rendertime": 0,
                    "error": None,
                    "messageError": ""
                }

                os.remove(filePath)

                print(resp)

                post_url = "http://tartarus2-env.eba-pqv9pzt9.us-east-2.elasticbeanstalk.com/v1/process/addProcess"

                requests.post(post_url, data=json.dumps(resp), headers={'Content-Type': 'application/json'})

    def post_name(self, cookie, tipoPessoa, document, viewState):
        JSESSIONID = ""
        for it in cookie:
            if it["name"] == "JSESSIONID":
                JSESSIONID = it["value"]

        cookies = {
            'JSESSIONID': JSESSIONID,
        }

        print(viewState)

        headers = {
            'Connection': 'keep-alive',
            'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="96", "Google Chrome";v="96"',
            'sec-ch-ua-mobile': '?0',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Accept': 'application/xml, text/xml, */*; q=0.01',
            'Faces-Request': 'partial/ajax',
            'X-Requested-With': 'XMLHttpRequest',
            'sec-ch-ua-platform': '"macOS"',
            'Origin': 'https://certidao.trt3.jus.br',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Dest': 'empty',
            'Referer': 'https://certidao.trt3.jus.br/certidao/feitosTrabalhistas/aba1.emissao.htm;jsessionid=GfhMdniZTncwheNIZwfgFgfe',
            'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
        }

        data = {
            'javax.faces.partial.ajax': 'true',
            'javax.faces.source': 'form:inputCNPJ',
            'javax.faces.partial.execute': 'form:inputCNPJ',
            'javax.faces.partial.render': 'form:nomeConsulta form:nomeReceitaCPF form:nomeReceitaCNPJ form:botaoConsultar',
            'javax.faces.behavior.event': 'change',
            'javax.faces.partial.event': 'change',
            'form': 'form',
            'form:tipoPessoa': tipoPessoa,
            'form:inputCNPJ': document,
            'form:nomeReceitaCNPJ': '',
            'form:nomeConsulta': '',
            'form:verifyCaptcha_': '',
            'javax.faces.ViewState': viewState
        }

        response = requests.post('https://certidao.trt3.jus.br/certidao/feitosTrabalhistas/aba1.emissao.htm', headers=headers, cookies=cookies, data=data)

        print(response.status_code)
        print(response.content)

        #self.driver.save_screenshot('captcha 5.png')

        data = {
            'javax.faces.partial.ajax': 'true',
            'javax.faces.source': 'form:inputCNPJ',
            'javax.faces.partial.execute': 'form:inputCNPJ',
            'javax.faces.partial.render': 'form:nomeConsulta form:nomeReceitaCPF form:nomeReceitaCNPJ form:botaoConsultar',
            'javax.faces.behavior.event': 'change',
            'javax.faces.partial.event': 'change',
            'form': 'form',
            'form:tipoPessoa': 'J',
            'form:inputCNPJ': '33.061.813/0001-40',
            'form:nomeReceitaCNPJ': 'PRUDENTIAL DO BRASIL SEGUROS DE VIDA S.A.',
            'form:nomeConsulta': '',
            'form:verifyCaptcha_': '',
            'javax.faces.ViewState': viewState,
        }

        response = requests.post('https://certidao.trt3.jus.br/certidao/feitosTrabalhistas/aba1.emissao.htm', headers=headers, cookies=cookies, data=data)
        print(response.status_code)
        print(response.content)

        return