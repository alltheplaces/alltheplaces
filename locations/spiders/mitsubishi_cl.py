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
            location_type = location.xpath(".//@data-servicios").get()
            if "ventas" not in location_type:
                if "repuestos" in location_type:
                    apply_category(Categories.SHOP_CAR_PARTS, item)
                    apply_yes_no(Extras.CAR_REPAIR, item, "servicios" in location_type)
                else:
                    apply_category(Categories.SHOP_CAR_PARTS, item)
            else:
                apply_category(Categories.SHOP_CAR, item)
                apply_yes_no(Extras.CAR_REPAIR, item, "servicios" in location_type)
                apply_yes_no(Extras.CAR_PARTS, item, "Repuestos" in location_type)

            yield item
