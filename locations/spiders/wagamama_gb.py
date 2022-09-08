# -*- coding: utf-8 -*-
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from locations.linked_data_parser import LinkedDataParser
from locations.microdata_parser import MicrodataParser


class WagamamaGBSpider(CrawlSpider):
    name = "wagamama_gb"
    item_attributes = {"brand": "Wagamama", "brand_wikidata": "Q503715"}
    allowed_domains = ["wagamama.com"]
    start_urls = ["https://www.wagamama.com/restaurants/"]
    rules = [Rule(LinkExtractor(allow="/restaurants/"), callback="parse", follow=True)]
    download_delay = 0.5

    def parse(self, response):
        MicrodataParser.convert_to_json_ld(response)
        yield LinkedDataParser.parse(response, "Restaurant")
