import scrapy
from scrapy.spiders import BaseSpider
from locations.items import GeojsonPointItem
import json
import re
from io import StringIO
from scrapy.http import HtmlResponse
from xml.dom import minidom

default_headers = {
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_1) AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/63.0.3239.84 Safari/537.36"}


class ATTScraper(scrapy.Spider):
    name = "toysrus"

    start_urls = ['https://www.att.com/sitemapfiles/stores-sitemap.xml']

    def parse(self, response):
        document = minidom.parseString(response.body_as_unicode())
        for loc in document.getElementsByTagName("loc"):

