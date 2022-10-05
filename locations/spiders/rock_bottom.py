# -*- coding: utf-8 -*-
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from locations.linked_data_parser import LinkedDataParser


class RockBottomSpider(CrawlSpider):
    name = "rock_bottom"
    item_attributes = {"brand": "Rock Bottom", "brand_wikidata": "Q73504866"}
    allowed_domains = ["rockbottom.com"]
    download_delay = 0.5
    start_urls = ["https://www.rockbottom.com/locations"]
    rules = [Rule(LinkExtractor(allow="/locations/"), callback="parse", follow=False)]

    def parse(self, response):
        if item := LinkedDataParser.parse(response, "Restaurant"):
            item["ref"] = response.url
            yield item
