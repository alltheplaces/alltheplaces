import re
from typing import Any

from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Request, Rule

from locations.hours import DAYS_3_LETTERS
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class FatfaceSpider(CrawlSpider):
    name = "fatface"
    item_attributes = {"brand": "FATFACE", "brand_wikidata": "Q5437186"}
    start_urls = ["https://www.fatface.com/countryselect"]
    rules = [
        Rule(LinkExtractor(allow="https://www.fatface.com/[a-z]{2}/en"), callback="parse"),
    ]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        yield Request(url=f'{response.url.strip("/")}/store-locator', callback=self.parse_stores)

    def parse_stores(self, response: Response, **kwargs: Any) -> Any:
        for store in response.xpath('//li[@class="vs-store"]'):
            item = Feature()
            item["ref"] = item["branch"] = store.xpath(".//button/strong/text()").get()
            store_details = store.xpath('.//*[@class="vs-store-address"]/text()').getall()
            hours_start_index = len(store_details)
            for index, info in enumerate(store_details):
                if any(day in info for day in DAYS_3_LETTERS):
                    hours_start_index = index
                    break
            address = store_details[:hours_start_index]
            # check for phone
            if not re.search(r"[A-Za-z]+", address[-1]):
                item["phone"] = address[-1]
                address = address[:-1]
            item["addr_full"] = clean_address(address)
            item["country"] = response.url.split("/")[3]
            yield item
