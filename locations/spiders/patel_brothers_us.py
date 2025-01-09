from typing import Any

import scrapy
from scrapy.http import Response

from locations.items import Feature
from locations.storefinders.super_store_finder import SuperStoreFinderSpider


class PatelBrothersUSSpider(scrapy.Spider):
    name = "patel_brothers_us"
    item_attributes = {"brand": "Patel Brothers", "brand_wikidata": "Q55641396"}
    start_urls = ["https://www.patelbros.com/locations"]
    no_refs = True


    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.xpath('//*[@id="distance-location"]//*[@class="w-dyn-item"]'):
            item = Feature()
            item["branch"] = store.xpath('.//h2/text()').get().removeprefix("Patel Brothers ")
            item["city"] = store.xpath('.//*[@class="display-inline"][1]/text()').get()
            item["state"] = store.xpath('.//*[@class="display-inline"][2]/text()').get()
            item["postcode"] = store.xpath('.//*[@class="display-inline"][3]/text()').get()
            item["addr_full"] = store.xpath('.//*[@class= "location-map-subheading"]/text()').get()
            item["lat"] = store.xpath('.//*[@class= "location_lat lat w-condition-invisible"]/text()').get()
            item["lon"] = store.xpath('.//*[@class= "location_long lon w-condition-invisible"]/text()').get()
            item["email"] = store.xpath('.//*[@class= "location-info_email"]/text()').get()
            item["phone"] = store.xpath('.//*[@class= "location-info_phone"]/text()').get()
            yield item
