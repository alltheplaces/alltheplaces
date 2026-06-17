from copy import deepcopy
from typing import Any

import scrapy
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.google_url import extract_google_position
from locations.items import Feature


class MitsubishiMASpider(scrapy.Spider):
    name = "mitsubishi_ma"
    item_attributes = {"brand": "Mitsubishi", "brand_wikidata": "Q36033"}
    start_urls = ["http://www.mitsubishi-motors.ma/succursale"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.xpath('//*[@class="item-list"]//li'):
            item = Feature()
            item["ref"] = location.xpath('.//*[contains(@class,"more-infos")]/@id').get("")
            item["branch"] = location.xpath(".//h3/text()").get()
            item["street_address"] = location.xpath('.//*[@class="adrs"]//p/text()[1]').get("").strip()
            item["city"] = location.xpath('.//*[@class="adrs"]//p/text()[2]').get("").strip()
            item["phone"] = location.xpath('.//*[contains(@href,"tel:")]/text()').get()
            extract_google_position(item, location)

            has_sales = bool(location.xpath('.//*[contains(@class,"vente")]'))
            has_services = bool(location.xpath('.//*[contains(@class,"services")]'))

            if has_sales:
                sales_item = deepcopy(item)
                sales_item["ref"] = f"{item['ref']}-sales"
                apply_category(Categories.SHOP_CAR, sales_item)
                yield sales_item

            if has_services:
                service_item = deepcopy(item)
                service_item["ref"] = f"{item['ref']}-service"
                apply_category(Categories.SHOP_CAR_REPAIR, service_item)
                yield service_item
