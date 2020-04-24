# -*- coding: utf-8 -*-
import time
import re
import json
import pickle

import scrapy
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from ArticleSpider.settings import COOKIES_STORE
import os


class TianYaSpider(CrawlSpider):
    name = 'tianya'
    #allowed_domains = ['https://bbs.tianya.cn/']
    start_urls = ['https://bbs.tianya.cn/']

    _cookie_path = COOKIES_STORE + '/tianya.cookie'

    def __init__(self, name=None, **kwargs):
        super().__init__(name=None, **kwargs)
        chrome_option = Options()
        chrome_option.add_argument('--disable-extensions')
        #chrome_option.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
        self.browser = webdriver.Chrome()

    def parse_search(self, response):
        currentPage = int((response.url).split("pn=")[-1])
        texts = response.xpath("//div[@class='searchListOne']//div").extract()
        for text in texts:
            urls = []
            text = text.split("\n")
            text = " ".join(text)
            reg = re.compile('.*href=\"(http://.*\.shtml)\".*')
            if re.match(reg, text):
                m1 = reg.findall(text)
                yield scrapy.Request(
                    url=m1[0],
                    callback=self.parse_detail
                )

        nextText = response.xpath("//div[@class='long-pages']").extract()[0]
        nextText = re.sub(r'\s*', "", nextText)
        nextText = [i for i in re.sub(r'<[^>]+>', "\n", nextText).split("\n") if i != ""]
        lastPage = int(nextText[-2])
        if currentPage < lastPage:
            yield scrapy.Request(
                url=(response.url).split("&pn=")[0]+"&pn="+str(currentPage+1),
                callback=self.parse_search
            )

    def parse_detail(self, response):
        title = response.xpath("//span[@class='s_title']").extract()
        title = response.xpath("//div[@class='q-title']").extract() if len(title) < 1 else None
        title = re.sub(r'<[^>]+>',"", title[0]) if title !=None else title
        title = re.sub(r'\s*', "", title) if title !=None else title

        mainContent = response.xpath("//div[@class='bbs-content clearfix']").extract()
        mainContent = re.sub(r'<[^>]+>',"",mainContent[0]) if len(mainContent)>0 else None
        mainContent = re.sub(r'\s*', "", mainContent) if mainContent != None else mainContent
        print(mainContent)


        #print(title)
        comments = []
        commentItems = response.xpath("//div[@class='atl-item']").extract()
        for i in commentItems:
            text = " ".join(i.split("\n"))
            reg = re.compile('.*<div class="bbs-content">(.*)</div>.*')
            if re.match(reg, text):
                m1 = reg.findall(text)[0]
                m1 = re.sub(r'\s*', "",m1)
                index = m1.find("</div>")
                m1 = re.sub(r'\s*', "", m1[:index])
                m1 = re.sub(r'<[^>]+>',"",m1)
                comments.append(m1)


        return

    def start_requests(self):
        self.browser.get(self.start_urls[0])
        self.browser.find_element_by_xpath("//input[@name='q']").send_keys(Keys.CONTROL + 'a')
        self.browser.find_element_by_xpath("//input[@name='q']").send_keys('单身狗')
        time.sleep(0.44)
        self.browser.execute_script("document.getElementsByClassName('top-search-submit')[0].click()")


        yield scrapy.Request(
            url=self.browser.current_url+"&pn=1",
            callback=self.parse_search
        )


