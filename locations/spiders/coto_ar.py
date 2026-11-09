import json
import re
from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class CotoARSpider(JSONBlobSpider):
    name = "coto_ar"
    item_attributes = {"brand": "Coto", "brand_wikidata": "Q5175411"}
    start_urls = ["https://www.coto.com.ar/sucursales/"]

    def extract_json(self, response: TextResponse) -> list[dict]:
        regions = json.loads(re.search(r"SOURCE_DATA\s*=\s*(\[.*?\n\]);", response.text, re.S).group(1))
        return [store for region in regions for store in region["rows"]]

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["sucursal"]
        item["branch"] = item.pop("name")

        item["opening_hours"] = OpeningHours()
        for days, hours in [
            (DAYS[:4], feature["lunesAJueves"]),
            (["Fr"], feature["viernes"]),
            (["Sa"], feature["sabado"]),
            (["Su"], feature["domingo"]),
        ]:
            for day in days:
                if hours.upper() == "CERRADO":
                    item["opening_hours"].set_closed(day)
                else:
                    item["opening_hours"].add_range(day, *hours.split(" a "))

        apply_category(Categories.SHOP_SUPERMARKET, item)
        yield item
