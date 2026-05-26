from copy import deepcopy
from typing import Any

import scrapy
from scrapy.http import Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.google_url import extract_google_position
from locations.items import Feature


class MitsubishiCLSpider(scrapy.Spider):
    name = "mitsubishi_cl"
    item_attributes = {
        "brand": "Mitsubishi",
        "brand_wikidata": "Q36033",
    }
    start_urls = ["https://mitsubishi-motors.cl/encuentranos/"]
    no_refs = True

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.xpath('//*[@class="sucursal card shadow my-4"]'):
            item = Feature()
            item["branch"] = location.xpath(".//h3/text()").get()
            item["street_address"] = location.xpath(".//tbody//a/text()").get()
            item["city"] = location.xpath(".//tr[6]/td/text()").get()
            item["phone"] = location.xpath('.//*[contains(@href,"tel:")]/text()').get()
            extract_google_position(item, location)
            location_type = location.xpath(".//@data-servicios").get() or ""

            has_sales = "ventas" in location_type
            has_service = "servicios" in location_type or "servicio_Express" in location_type
            has_parts = "repuestos" in location_type

            if has_sales:
                sales_item = deepcopy(item)
                apply_category(Categories.SHOP_CAR, sales_item)
                apply_yes_no(Extras.CAR_REPAIR, sales_item, has_service)
                apply_yes_no(Extras.CAR_PARTS, sales_item, has_parts)
                yield sales_item

            if has_service:
                service_item = deepcopy(item)
                apply_category(Categories.SHOP_CAR_REPAIR, service_item)
                apply_yes_no(Extras.CAR_PARTS, service_item, has_parts)
                yield service_item

            if has_parts:
                parts_item = deepcopy(item)
                apply_category(Categories.SHOP_CAR_PARTS, parts_item)
                yield parts_item
