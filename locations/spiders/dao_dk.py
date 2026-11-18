import json
import re
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category, apply_yes_no
from locations.hours import DAYS, OpeningHours
from locations.items import Feature

DAY_KEYS = ["man", "tir", "ons", "tor", "fre", "lor", "son"]


class DaoDKSpider(Spider):
    name = "dao_dk"
    item_attributes = {"operator": "Dao", "operator_wikidata": "Q12307379"}
    allowed_domains = ["dao.as"]
    # Dao, Denmark's letter carrier since PostNord stopped letters in 2026, puts a letter box in every
    # daoSHOP (https://dao.as/brevkasser2026/). The shop finder embeds every shop in the page.
    start_urls = ["https://dao.as/find-daoshop/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        data = re.search(r"var STORE_LOCATIONS = (\{.*?\});", response.text, re.DOTALL)
        for shop in json.loads(data.group(1))["locations"]:
            item = Feature()
            item["ref"] = shop["shopId"]
            item["located_in"] = shop["navn"]
            item["lat"], item["lon"] = shop["latitude"], shop["longitude"]
            item["street_address"] = shop["adresse"]
            item["postcode"] = shop["postnr"]
            item["city"] = shop["bynavn"]
            # The letter box is reachable while the shop is open.
            item["opening_hours"] = self.parse_hours(shop.get("aabningstider") or {})
            apply_category(Categories.POST_BOX, item)
            apply_yes_no("indoor", item, True)
            yield item

    @staticmethod
    def parse_hours(hours: dict) -> OpeningHours:
        oh = OpeningHours()
        for key, day in zip(DAY_KEYS, DAYS):
            if m := re.fullmatch(r"\s*(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})\s*", hours.get(key) or ""):
                oh.add_range(day, m.group(1), m.group(2))
        return oh
