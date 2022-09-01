# -*- coding: utf-8 -*-
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from locations.microdata_parser import MicrodataParser
from locations.linked_data_parser import LinkedDataParser


class NisaLocalGBSpider(CrawlSpider):
    name = "nisalocal_gb"
    item_attributes = {"brand": "Nisa Local", "brand_wikidata": "Q16999069"}
    allowed_domains = ["nisalocally.co.uk"]
    start_urls = ["https://www.nisalocally.co.uk/stores/index.html"]
    rules = [Rule(LinkExtractor(allow=".*/stores/.*"), callback="parse", follow=True)]
    download_delay = 0.5

    def parse(self, response):
        MicrodataParser.convert_to_json_ld(response.selector)
        item = LinkedDataParser.parse(response, "ConvenienceStore")
        if item:
            yield item
