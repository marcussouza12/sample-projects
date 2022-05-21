import datetime
import json
import os
import time

import requests
import scrapy
from scrapy.utils.project import get_project_settings
from selenium import webdriver
from twocaptcha import TwoCaptcha

from sc_custom_image.spiders.common.util import modifyCNPJ, modifyCPF


class Trt5SPSpider(scrapy.Spider):
    name = 'trt5'
    start_urls = ['http://quotes.toscrape.com/js']

    def __init__(self, id='', code='', docType=''):
        self.settings = get_project_settings()
        self.chromePath = self.settings.get("CHROME_PATH")
        self.bucketName = self.settings.get("CERTIFICATION_BUCKET")

        ROOT_DIR = os.path.abspath(os.curdir)
        self.downloadPath = ROOT_DIR + "/temp"
        print(self.downloadPath)
        # os.makedirs(downloadPath)

        options = webdriver.FirefoxOptions()
        #options.add_argument("--ignore-certificate-erros")
        #options.add_argument("--headless")
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

        result = [
            {"code":"12917064706"}
        ]

        for q in result:
            self.driver.get("https://www.trt5.jus.br/certidao-eletronica/1")
            print(self.driver.current_url)
            time.sleep(3)

            self.type = "CNPJ"
            document = modifyCPF(q["code"])
            if len(q["code"]) != 11:
                self.driver.execute_script("document.querySelector('#edit-radios > div:nth-child(2) > label').click()")
                time.sleep(1)
                document = modifyCNPJ(q["code"],"COMPLETED")

            self.driver.find_element_by_name("documento").send_keys(document)
            time.sleep(1)

            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

            api_key = os.getenv('APIKEY_2CAPTCHA', self.settings.get("CLIENT_KEY_2_CAPTCHA"))

            solver = TwoCaptcha(api_key)

            result = solver.solve_captcha(
                site_key='6LcKIaEdAAAAAEClgzAPw3q_Bky9-1Ga4sB8M2KA',
                page_url=self.driver.current_url,
            )

            print(result)
            print("==========")

            #self.driver.execute_script("document.getElementsByName('h-captcha-response')[0].value = '" + result["code"] + "'")
            self.driver.execute_script("""document.querySelector('[name="g-recaptcha-response"]').innerText='{}'""".format(result))
            time.sleep(2)
            self.driver.find_element_by_id("edit-verificar").click()
            time.sleep(2)

            self.driver.find_element_by_id("trt5-ceat-emitir").click()
            time.sleep(7)

            filenames = next(os.walk(self.downloadPath), (None, None, []))[2]
            print(filenames)

            filePath = self.downloadPath + "/" + filenames[0]

            if self.id != '':
                name = self.informations["certificationRequest"]["document"] + "_" + datetime.date.today().strftime(
                    "%d_%m_%Y") + ".pdf"

                fileName = f'Certidoes/TRT5/{self.informations["certificationRequest"]["document"]}/{name}'

                '''post_data = {
                    "number": number,
                    "court": "TJSE",
                    "link": filename,
                    "description": move["descricao"],
                    "data": move["data"]
                }
                print(post_data)
    
                responseFile = requests.post(env + "/v1/midia/htmlToPDF",
                                             data=json.dumps(post_data),
                                             headers={"content-type": "application/json"})
                                             
                s3_client().upload_file(filePath, self.bucketName, fileName)
                print(filePath)
                print(tika_parser(filePath,''))

                post_data = {
                    "certificationId": self.informations["id"],
                    "path": fileName,
                    "content": tika_parser(filePath,'')
                }

                os.remove(filePath)
                                             
                                             '''

                post_data = {
                    "certificationId": self.informations["id"],
                    "path": fileName
                }

                response = requests.post(self.env + "/v1/certification/upload",
                                         headers={
                                             "x-api-key": "258a0b3c88dbf701892b713a91b793d5",
                                             "x-user": "marcussouza@id.uff.br",
                                             "Content-Type": "application/json",
                                         },
                                         data=json.dumps(post_data))

            else:
                #filePath = self.downloadPath + "/CEAT-trt3-33061813011770.pdf"
                text = self.driver.window_handles[1]
                processes = []
                for word in text:
                    print(word)
                    if len(word) == 20:
                        if "505" in word:
                            processes.append(word)

                print(q)
                resp = {
                    "radarId": q["id"],
                    "processes": processes,
                    "court": "TRT5Ceat",
                    "uid": q["uid"],
                    "userLogged": "ANONYMOUS",
                    "rendertime": 0,
                    "error": None,
                    "messageError": ""
                }

                # os.remove(filePath)

                print(resp)

                post_url = "http://tartarus2-env.eba-pqv9pzt9.us-east-2.elasticbeanstalk.com/v1/process/addProcess"

                requests.post(post_url, data=json.dumps(resp), headers={'Content-Type': 'application/json'})

    def post_name(selfs, cookie, tipoPessoa, document, viewState):
        JSESSIONID = ""
        for it in cookie:
            if it["name"] == "JSESSIONID":
                JSESSIONID = it["value"]

        cookies = {
            'JSESSIONID': JSESSIONID,
        }

        headers = {
            'Connection': 'keep-alive',
            'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="96", "Google Chrome";v="96"',
            'sec-ch-ua-mobile': '?0',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.55 Safari/537.36',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Accept': 'application/xml, text/xml, */*; q=0.01',
            'Faces-Request': 'partial/ajax',
            'X-Requested-With': 'XMLHttpRequest',
            'sec-ch-ua-platform': '"macOS"',
            'Origin': 'https://certidao.trt3.jus.br',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Dest': 'empty',
            'Referer': 'https://certidao.trt3.jus.br/certidao/feitosTrabalhistas/aba1.emissao.htm',
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

        requests.post('https://certidao.trt3.jus.br/certidao/feitosTrabalhistas/aba1.emissao.htm', headers=headers, cookies=cookies, data=data)

        return