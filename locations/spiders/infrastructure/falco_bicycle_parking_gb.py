import re
from typing import Any

import chompjs
from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature


class FalcoBicycleParkingGBSpider(Spider):
    name = "falco_bicycle_parking_gb"
    item_attributes = {
        "brand": "Falco",
        "brand_wikidata": "Q138302109",
        "operator": "Falco",
        "operator_wikidata": "Q138302109",
        "country": "GB",
        "nsi_id": "N/A",
        "extras": {
            "bicycle_parking": "shed",
            "access": "permit",
        },
    }
    start_urls = ["https://rentals.falco.co.uk"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        js_text = response.xpath("//script[contains(text(), 'googlemaps.locations')]/text()").get()
        if not js_text:
            return
        if match := re.search(r"googlemaps\.locations\s*=\s*(\[.*\]);", js_text, re.DOTALL):
            for location in chompjs.parse_js_object(match.group(1)):
                item = Feature()
                item["ref"] = location[0]
                item["branch"] = location[1]
                item["lat"] = location[3]
                item["lon"] = location[4]
                item["street"] = location[5] or None
                item["postcode"] = location[7]
                item["city"] = location[8]
                item["extras"]["capacity"] = str(location[12])
                item["image"] = f"https://rentals.falco.co.uk{location[20]}"

                apply_category(Categories.BICYCLE_PARKING, item)
                yield item
