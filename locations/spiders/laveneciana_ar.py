from typing import Any, Iterable

import chompjs
from scrapy.http import Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import DAYS_ES, DELIMITERS_ES, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class LavenecianaARSpider(JSONBlobSpider):
    name = "laveneciana_ar"
    item_attributes = {"brand": "La Veneciana"}
    allowed_domains = ["laveneciana.com.ar"]
    start_urls = ["https://laveneciana.com.ar/nuestras-sucursales/"]

    def extract_json(self, response: Response) -> Any:
        data = response.xpath('//script[contains(text(), "var php_vars =")]/text()').get().split("var php_vars = ")[1]
        return chompjs.parse_js_object(data)["sucursales"]

    def pre_process_data(self, feature: dict) -> None:
        feature["direccion"] = feature["direccion"].replace(" | ", ", ")

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(
            feature.get("dias_horarios") or "", days=DAYS_ES, delimiters=DELIMITERS_ES
        )
        apply_yes_no(Extras.WIFI, item, feature.get("wifi") == "si")
        apply_category(Categories.ICE_CREAM, item)
        yield item
