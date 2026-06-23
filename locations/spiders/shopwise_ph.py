import re
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class ShopwisePHSpider(Spider):
    name = "shopwise_ph"
    item_attributes = {"brand": "Shopwise", "brand_wikidata": "Q118674375"}
    allowed_domains = ["api.shopwise.com.ph"]
    start_urls = ["https://api.shopwise.com.ph/api/web/our-stores?site_id=2"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        ph_regions = {
            region["id"]: re.sub(r"^Region [\w\-]+ \(([^\)]+)\)$", r"\1", region["name"]).title()
            for region in response.json()["perRegions"]
        }
        for location in response.json()["branches"]:
            if not location.get("enabled"):
                continue
            item = DictParser.parse(location)
            item["branch"] = item.pop("name")
            item["phone"] = re.sub(
                r"<[^>]+>", "", location["phone"].split(" loc", 1)[0].split(";", 1)[0].split("/", 1)[0]
            )
            item["state"] = ph_regions[location["region_id"]]
            hours_string = "Mo-Su: " + re.sub(r"<[^>]+>", "", location.get("store_hours", ""))
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(hours_string)

            apply_category(Categories.SHOP_SUPERMARKET, item)

            yield item
