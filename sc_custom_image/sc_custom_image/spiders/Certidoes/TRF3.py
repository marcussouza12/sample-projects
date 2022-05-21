import json
import os
import time

import requests
import scrapy
from scrapy.utils.project import get_project_settings
from selenium import webdriver
from selenium.webdriver.common.by import By
from captcha_solver import CaptchaSolver


class TRF3Spider(scrapy.Spider):
    name = 'trf3'
    start_urls = ['http://quotes.toscrape.com/js']

    def __init__(self, *args, **kwargs):
        self.settings = get_project_settings()
        self.chromePath = self.settings.get("CHROME_PATH")

        ROOT_DIR = os.path.abspath(os.curdir)
        downloadPath = ROOT_DIR
        print(downloadPath)
        #os.makedirs(downloadPath)

        options = webdriver.ChromeOptions()
        # options.add_argument("--disable-extensions")
        # options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")

        options.add_experimental_option("prefs", {
            "download.default_directory": downloadPath,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing_for_trusted_sources_enabled": False,
            "safebrowsing.enabled": False
        })

        self.driver = webdriver.Chrome(chrome_options=options, executable_path=self.chromePath)

    def parse(self, response):
        self.driver.get("http://web.trf3.jus.br/certidao/Certidao/Solicitar")
        print(self.driver.current_url)
        time.sleep(4)

        self.driver.execute_script('document.getElementById("Nome").value = "Marcus Paulo Ferreira de Souza"')
        self.driver.execute_script('document.getElementById("CpfCnpj").value = "12917064706"')
        self.driver.execute_script('document.getElementById("frm").submit()')

        self.driver.execute_script('document.getElementById("abrangenciaTRF").checked = true')
        self.driver.execute_script('document.getElementById("frm").submit()')
        time.sleep(2)

        #self.driver.execute_script('document.getElementById("abrangenciaTRF").checked = true')
        #self.driver.execute_script('document.getElementById("frm").submit()')
        #time.sleep(2)




