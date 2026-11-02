import re
from collections import Counter
from typing import Any

from scrapy.http import Response
from scrapy.spiders import Spider

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature


class CondisESSpider(Spider):
    name = "condis_es"
    item_attributes = {"brand": "Condis", "brand_wikidata": "Q57417581"}
    start_urls = ["https://www.condis.es/wp-content/uploads/condis/stores-finder-es.json"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        data = response.json()
        phones = Counter(store[8] for store in data["stores"])
        for ref, store in enumerate(data["stores"]):
            if data["brands"][store[2]] == "condisline":
                continue
            item = Feature()
            item["ref"] = str(ref)
            item["city"] = data["places"][store[1]]
            item["postcode"] = store[4]
            item["street_address"] = store[5]
            item["lat"] = store[11]
            item["lon"] = store[12]
            if data["zones"][store[0]] == "and":
                item["country"] = "AD"
            if phones[store[8]] == 1:
                item["phone"] = store[8]

            days_hours = store[6] if isinstance(store[6], list) else [store[6]] * 7
            oh = OpeningHours()
            for day, hours in zip(DAYS, days_hours):
                if "cerrado" in hours.lower() and not re.search(r"\d", hours):
                    oh.set_closed(day)
                    continue
                for start, end in re.findall(r"(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})", hours):
                    oh.add_range(day, start, end)
            item["opening_hours"] = oh

            apply_category(Categories.SHOP_SUPERMARKET, item)
            yield item
