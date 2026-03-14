import re
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature


class OazisHUSpider(Spider):
    name = "oazis_hu"
    item_attributes = {"brand": "OÁZIS", "brand_wikidata": "Q20439720"}
    start_urls = ["https://oazis.hu/aruhazaink"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in re.findall(
            r"L\.latLng\(\s*'(-?\d+\.\d+)',\s*'( ?-?\d+\.\d+)',.+?getInfoBoxContent\(\s*'(.+?)',\s*'(.+?)',\s*'(.+?)',",
            response.text,
            re.DOTALL,
        ):
            item = Feature()
            item["lat"], item["lon"], item["branch"], item["addr_full"], item["website"] = location
            item["ref"] = item["website"]

            apply_category(Categories.SHOP_GARDEN_CENTRE, item)

            yield item
