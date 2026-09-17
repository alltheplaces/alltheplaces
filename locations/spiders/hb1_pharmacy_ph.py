from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature


class Hb1PharmacyPHSpider(Spider):
    name = "hb1_pharmacy_ph"
    item_attributes = {"brand_wikidata": "Q120350751"}
    start_urls = ["https://nccc.com.ph/business-unit/hb1-pharmacy/"]
    no_refs = True
    requires_proxy = True

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.xpath('//ul[@class="contact"]/parent::div/parent::div'):
            item = Feature()
            item["name"] = location.xpath(".//span/text()").get()
            item["addr_full"] = location.xpath('//li[@class="address"]/text()').get()
            item["phone"] = location.xpath('//li[@class="contact-number"]/text()').get()
            item["email"] = location.xpath('//li[@class="email"]/text()').get()
            apply_category(Categories.SHOP_CHEMIST, item)
            yield item
