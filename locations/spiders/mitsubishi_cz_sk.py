import re
from copy import deepcopy
from typing import Any

import chompjs
from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class MitsubishiCZSKSpider(Spider):
    name = "mitsubishi_cz_sk"
    item_attributes = {"brand": "Mitsubishi", "brand_wikidata": "Q36033"}
    start_urls = ["https://www.mitsubishi-motors.cz/prodejci/", "https://www.mitsubishi-motors.sk/predajcovia/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in chompjs.parse_js_object(
            response.xpath('//script[contains(text(), "var locations")]/text()').get()
        ):
            item = DictParser.parse(location)
            yield response.follow(
                url=location["url"],
                callback=self.parse_location_details,
                cb_kwargs=dict(item=item, location_type=location["type"]),
            )

    def parse_location_details(self, response: Response, item: Feature, location_type: str) -> Any:
        location = response.xpath(f'//*[@class="dealer-info dealer_info_{item["ref"]}"]//*[@class="dealer-detail"]')
        address = location.xpath(".//p[1]/text()").getall()
        address_end_index = -1
        for index, text in enumerate(address):
            if "IČ:" in text:
                address_end_index = index
                break
        item["addr_full"] = clean_address(address[:address_end_index])

        if phone := re.search(r"Telef[oó]n:(.+?)<", location.get("")):
            item["phone"] = phone.group(1).replace(",", ";")

        item["email"] = location.xpath('.//a[contains(@href,"mailto:")]/@href').get()
        item["website"] = location.xpath('.//a[contains(text(), "webová stránka")]/@href').get()
        item["extras"]["brand:website"] = response.url

        has_sales = "prodej" in location_type
        has_service = "servis" in location_type

        if has_sales:
            sales_item = deepcopy(item)
            sales_item["ref"] = f"{item['ref']}-sales"
            apply_category(Categories.SHOP_CAR, sales_item)
            yield sales_item

        if has_service:
            service_item = deepcopy(item)
            service_item["ref"] = f"{item['ref']}-service"
            apply_category(Categories.SHOP_CAR_REPAIR, service_item)
            yield service_item

        if not has_sales and not has_service:
            yield item
