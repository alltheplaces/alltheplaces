import json
import re
from typing import Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature


class TymebankZASpider(Spider):
    name = "tymebank_za"
    item_attributes = {"brand": "TymeBank", "brand_wikidata": "Q65066197"}
    start_urls = ["https://gotyme.co.za/api/1/services/kiosks.json"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response: Response) -> Iterable[Feature]:
        for data in json.loads(response.json()).get("kiosks"):
            item = Feature()
            item["branch"] = item["ref"] = data.get("branch_s")
            item["addr_full"] = data.get("address_s")
            item["city"] = data.get("city_s")
            if lat_lon := re.search(r"\+(-?\d+\.\d+)%2C(\d+\.\d+)", data.get("maplink_s")):
                item["lat"] = lat_lon.group(1)
                item["lon"] = lat_lon.group(2)
            apply_category(Categories.VENDING_MACHINE, item)
            yield item
