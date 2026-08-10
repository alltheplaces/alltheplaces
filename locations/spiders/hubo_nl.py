import json
from typing import Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours
from locations.items import Feature


class HuboNLSpider(Spider):
    name = "hubo_nl"
    item_attributes = {"brand": "Hubo", "brand_wikidata": "Q5473953", "extras": Categories.SHOP_DOITYOURSELF.value}
    start_urls = ["https://www.hubo.nl/winkels"]
    requires_proxy = True

    def parse(self, response: Response) -> Iterable[Feature]:
        for script in response.xpath("//script/text()").getall():
            if '"stores"' not in script[:50]:
                continue
            for store in json.loads(script)["stores"]:
                item = DictParser.parse(store)
                item["branch"] = item.pop("name")
                item["street_address"] = store["street_and_number"]

                oh = OpeningHours()
                for rule in store.get("opening_hours", []):
                    day = DAYS[rule["dayOfWeek"] - 1]
                    for i in range(1, 3):
                        if rule.get(f"from{i}") and rule.get(f"to{i}"):
                            oh.add_range(day, rule[f"from{i}"], rule[f"to{i}"])
                item["opening_hours"] = oh

                yield item
            return
