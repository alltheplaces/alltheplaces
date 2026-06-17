import re
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.hours import DAYS_3_LETTERS, OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class FatfaceIESpider(Spider):
    name = "fatface_ie"
    item_attributes = {"brand": "Fat Face", "brand_wikidata": "Q5437186"}
    start_urls = ["https://www.fatface.com/ie/en/store-locator"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.xpath('//li[@class="vs-store"]'):
            item = Feature()
            item["branch"] = store.xpath(".//button/strong/text()").get()
            store_details = store.xpath('.//*[@class="vs-store-address"]/text()').getall()
            hours_start_index = len(store_details)
            for index, info in enumerate(store_details):
                if any(day in info for day in DAYS_3_LETTERS):
                    hours_start_index = index
                    break
            address = store_details[:hours_start_index]
            if address and not re.search(r"[A-Za-z]+", address[-1]):
                item["phone"] = address[-1].strip()
                address = address[:-1]
            item["ref"] = item["addr_full"] = clean_address(address)
            item["country"] = "IE"
            item["website"] = response.url
            if hours_start_index < len(store_details):
                item["opening_hours"] = OpeningHours()
                for rule in store_details[hours_start_index:]:
                    item["opening_hours"].add_ranges_from_string(rule)
            yield item
