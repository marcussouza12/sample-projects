import datetime
import json
import os
import sys
import time
import traceback

import requests
import scrapy
from PIL import Image
from captcha_solver import CaptchaSolver
from scrapy.utils.project import get_project_settings
from selenium import webdriver
from selenium.webdriver.common.by import By
from twocaptcha import TwoCaptcha

from sc_custom_image.spiders.common.aws_util import s3_client
from sc_custom_image.spiders.common.util import modifyCPF, modifyCNPJ


class ReceitaFederalSpider(scrapy.Spider):
    name = 'receitaFederal'
    start_urls = ['http://quotes.toscrape.com/js']

    def __init__(self, id=''):
        self.settings = get_project_settings()
        self.chromePath = self.settings.get("CHROME_PATH")
        self.bucketName = self.settings.get("CERTIFICATION_BUCKET")

        self.ROOT_DIR = os.path.abspath(os.curdir)
        self.downloadPath = self.ROOT_DIR
        print(self.downloadPath)
        # os.makedirs(downloadPath)

        options = webdriver.FirefoxOptions()
        #options.add_argument("--enable-automation")
        #options.add_argument("--incognito")
        #options.add_argument("--disable-extensions")
        #options.add_argument("--headless")
        #options.add_argument("--disable-gpu")
        #options.add_argument("--no-sandbox")
        options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36 ")
        '''options.add_experimental_option("prefs", {
            "download.default_directory": self.downloadPath,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing_for_trusted_sources_enabled": False,
            "safebrowsing.enabled": False
        })

        prox = Proxy()
        prox.proxy_type = ProxyType.MANUAL
        prox.http_proxy = "marcussouza:ncPmzbga@160.116.130.229:55393"
        prox.socks_proxy = "marcussouza:ncPmzbga@160.116.130.229:55393"
        prox.ssl_proxy = "marcussouza:ncPmzbga@160.116.130.229:55393"

        capabilities = webdriver.DesiredCapabilities.CHROME
        prox.add_to_capabilities(capabilities)

        options.set_capability(capabilities)'''
        settings = get_project_settings()

        HEADLESS_PROXY = "9802902e2fe646869bf82fbe02c4ac93:@proxy.crawlera.com:8011"
        webdriver.DesiredCapabilities.FIREFOX['proxy'] = {
            "httpProxy": HEADLESS_PROXY,
            "sslProxy": HEADLESS_PROXY,
            "proxyType": "MANUAL",
        }

        #chrome_options=options,
        #self.driver = webdriver.Chrome(executable_path=ChromeDriverManager().install(),options=options)
        self.driver = webdriver.Firefox(executable_path=settings.get("FIREFOX_PATH"), options=options)

        params = {'behavior': 'allow', 'downloadPath': self.downloadPath}
        #self.driver.execute_cdp_cmd("Page.setDownloadBehavior", params)

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
        document = modifyCPF(informations["certificationRequest"]["document"])
        if informations["certificationRequest"]["documentType"] == 'CNPJ':
            site = 'PJ'
            document = modifyCNPJ(informations["certificationRequest"]["document"],"COMPLETED")

        print(site)

        self.driver.get(f"https://solucoes.receita.fazenda.gov.br/Servicos/certidaointernet/{site}/Emitir")
        print(self.driver.current_url)
        time.sleep(3)


        config = {
            "captchaInfo": { "captcha_service":  "CLIENT_KEY_2_CAPTCHA" }
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

        #init = self.init_captcha_service(config, captchas, '4a65992d-58fc-4812-8b87-789f7e7c4c4b', self.driver.current_url)
        #taskId = json.loads(init.content.decode("utf-8"))["request"]
        #response = self.recaptcha(taskId, captchas, config)

        api_key = os.getenv('APIKEY_2CAPTCHA', self.settings.get("CLIENT_KEY_2_CAPTCHA"))

        #solver = TwoCaptcha(api_key)

        '''try:
            result = solver.hcaptcha(
                sitekey='4a65992d-58fc-4812-8b87-789f7e7c4c4b',
                url=self.driver.current_url,
                invisible=0
            )

        except Exception as e:
            sys.exit(e)

        else:
            #sys.exit('solved: ' + str(result["code"]))
            print(result["code"])

            self.driver.execute_script("document.getElementsByName('h-captcha-response')[0].value = '" + result["code"] + "'")

        #content = self.driver.find_element_by_id('imgCaptchaSerpro')
        #content.screenshot('captcha.png')'''

        #solver = CaptchaSolver('2captcha', api_key=self.settings.get("CLIENT_KEY_2_CAPTCHA"))
        #raw_data = open('captcha.png', 'rb').read()
        #result = solver.solve_captcha(raw_data)

        #self.driver.find_element_by_id("txtTexto_captcha_serpro_gov_br").send_keys(result)

        #captcha = json.loads(response.content)["request"]
        #captcha = result["code"]
        #self.driver.execute_script("document.getElementsByTagName('textarea')[0].value= '" + captcha + "'")
        #self.driver.execute_script("document.getElementsByName('h-captcha-response')[0].dispatchEvent(new Event('submit'))")

        #print(self.driver.execute_script("document.getElementsByName('h-captcha-response')[0].value"))
        #self.driver.find_element_by_xpath('//*[@id="frmInfParam"]/div[3]/button').click()
        self.driver.save_screenshot("rf 0.png")

        time.sleep(3)
        self.driver.find_element(by=By.ID, value="NI").send_keys(document)
        #self.driver.execute_script("document.getElementById('NI').value = '" + document + "'")
        self.driver.execute_script("document.getElementById('NI').dispatchEvent(new Event('change'))")
        time.sleep(3)

        self.driver.find_element_by_id("validar").click()
        time.sleep(10)

        #self.search(site, informations)

        self.driver.save_screenshot("rf.png")

        print("*******")
        print(len(self.driver.find_elements_by_tag_name("html")[0].get_attribute("innerHTML").split(
            "Não foi possível concluir a ação para o contribuinte informado. Por favor, tente novamente dentro de alguns minutos")) > 1)
        if len(self.driver.find_elements_by_tag_name("html")[0].get_attribute("innerHTML").split(
                "Não foi possível concluir a ação para o contribuinte informado. Por favor, tente novamente dentro de alguns minutos")) > 1:
            time.sleep(60)
            data = {
                'project': '557019',
                'spider': 'receitaFederal',
                'id': self.id
            }

            requests.post('https://app.scrapinghub.com/api/run.json', data=data,
                          auth=('23be55028fa04ce8a0155b6b02493449', ''))
        else:

            try:
                self.driver.save_screenshot("rf1.png")
                print("help")
                #self.driver.find_element_by_xpath('//*[@id="FrmSelecao"]/a[2]').click()
                #time.sleep(20)

                filePath = self.downloadPath + f'/Certidao-{informations["certificationRequest"]["document"]}.pdf'
                while not os.path.exists(filePath):
                    time.sleep(1)
                if os.path.isfile(filePath):
                    print("File Downloaded successfully..")
                print(filePath)

            except:
                print("Exception")
                traceback.print_exc()

                self.driver.fullscreen_window()

                filePath = self.downloadPath + "/Certidao Aux.png"

                self.driver.save_screenshot(filePath)

                image1 = Image.open(filePath)
                im1 = image1.convert('RGB')
                filePath = self.downloadPath + "/Certidao Aux.pdf"
                im1.save(filePath)

                os.remove(self.downloadPath + "/Certidao Aux.png")

            name = informations["certificationRequest"]["document"] + "_" + datetime.date.today().strftime(
                "%d_%m_%Y") + ".pdf"
            fileName = f'Certidoes/Receita Federal/{informations["certificationRequest"]["document"]}/{name}'

            s3_client().upload_file(filePath, self.bucketName, fileName)
            print(filePath)

            #os.remove(filePath)

            post_data = {
                "certificationId": informations["id"],
                "path": fileName,
                "extraParameters": None
            }

            response = requests.post(self.env + "/v1/certification/upload",
                                     headers={
                                         "x-api-key": "258a0b3c88dbf701892b713a91b793d5",
                                         "x-user": "marcussouza@id.uff.br",
                                         "Content-Type": "application/json",
                                     },
                                     data=json.dumps(post_data))
            print(response.content)
            print(response.status_code)

    def search(self, site, informations):
        print("cheguei")
        execute = self.driver.find_element_by_id("dialog-message").get_attribute("hidden") == 'true'

        print(execute)
        while not execute:
            self.driver.get(f"https://servicos.receita.fazenda.gov.br/Servicos/certidaointernet/{site}/Emitir")
            print(self.driver.current_url)
            time.sleep(3)

            content = self.driver.find_element_by_id('imgCaptchaSerpro')
            content.screenshot('captcha.png')

            solver = CaptchaSolver('2captcha', api_key=self.settings.get("CLIENT_KEY_2_CAPTCHA"))
            raw_data = open('captcha.png', 'rb').read()
            result = solver.solve_captcha(raw_data)

            os.remove('captcha.png')

            self.driver.find_element_by_id("txtTexto_captcha_serpro_gov_br").send_keys(result)
            self.driver.execute_script("document.getElementById('NI').value = '" + modifyCPF(
                informations["certificationRequest"]["document"]) + "'")

            self.driver.find_element_by_id("validar").click()
            time.sleep(6)

            execute = self.driver.find_element_by_id("dialog-message").get_attribute("hidden") == 'true'
            print(execute)

        return

    def init_captcha_service(self,config, captchas, websiteKey, pageurl):
        return requests.post(url=f"{captchas['urlIn']}?key=" + self.settings.get(config["captchaInfo"]["captcha_service"]) +
                                 "&method=hcaptcha&sitekey=" + websiteKey + "&invisible=1&json=1&pageurl=" + pageurl)


    def recaptcha(self, taskId, captchas, config):
        response = requests.get(
            f"{captchas['urlRes']}?key=" + self.settings.get(config["captchaInfo"]["captcha_service"]) + "&action=get&json=1&id=" + taskId)

        print(response.content)
        captcha = json.loads(response.content.decode("utf-8"))

        value = 0
        while captcha["request"] == "CAPCHA_NOT_READY" and value < 150:
            time.sleep(1)
            value = value + 1

            response = requests.get(
                f"{captchas['urlRes']}?key=" + self.settings.get(config["captchaInfo"]["captcha_service"]) + "&action=get&json=1&id=" + taskId)

            captcha = json.loads(response.content.decode("utf-8"))
            print(captcha)


        return response
