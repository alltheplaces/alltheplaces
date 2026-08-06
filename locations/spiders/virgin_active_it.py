import re

from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.items import Feature
from locations.spiders.virgin_active_bw_na_za import VIRGIN_ACTIVE_SHARED_ATTRIBUTES


class VirginActiveITSpider(CrawlSpider):
    name = "virgin_active_it"
    item_attributes = VIRGIN_ACTIVE_SHARED_ATTRIBUTES
    start_urls = ["https://www.virginactive.it/club"]
    rules = [
        Rule(LinkExtractor(allow=r"/club/[-\w]+/[-\w]+$"), callback="parse"),
    ]

    def parse(self, response, **kwargs):
        item = Feature()
        item["branch"] = response.xpath("//h1/text()").get()
        item["addr_full"] = response.xpath('//*[@class="clubAddress d-none d-sm-block"]/text()').get()
        item["lat"] = re.search(r"latitude\":\s*(\d+,\d+)", response.text).group(1).replace(",", ".")
        item["lon"] = re.search(r"longitude\":\s*(\d+,\d+)", response.text).group(1).replace(",", ".")
        item["website"] = item["ref"] = response.url
        yield item
