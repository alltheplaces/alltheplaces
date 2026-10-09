from collections import defaultdict
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature


class PostaUgandaUGSpider(Spider):
    name = "posta_uganda_ug"
    item_attributes = {"operator": "Posta Uganda", "operator_wikidata": "Q7233761"}
    allowed_domains = ["api.ugapost.go.ug"]
    # Feed behind "Our Locations" at https://web.ugapost.go.ug/about-us/our-locations
    start_urls = ["https://api.ugapost.go.ug/api/postal-stations?page=1&limit=1000"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        stations = response.json()["data"]["rows"]

        # Several unrelated offices share one position (Gulu and Kitgum, Kabale and Kisoro, Koboko,
        # Moyo and Yumbe, ...): those positions are placeholders and are dropped. "Nateete" is
        # listed twice under two codes at one position: keep one.
        stacks = defaultdict(list)
        for station in stations:
            stacks[(station["latitude"], station["longitude"])].append(station)
        skip = set()
        placeholder = set()
        for position, stack in stacks.items():
            if len({s["name"].strip().lower() for s in stack}) > 1:
                placeholder.add(position)
            else:
                skip.update(s["id"] for s in stack[1:])

        for station in stations:
            if station["id"] in skip:
                continue
            item = Feature()
            item["ref"] = station["code"]
            item["branch"] = station["name"].strip()
            # The contact number is the head office switchboard for every station; not used.
            position = (station["latitude"], station["longitude"])
            if position not in placeholder and -1.5 < position[0] < 4.3 and 29.5 < position[1] < 35.1:
                item["lat"], item["lon"] = position
            item["extras"]["post_office:type"] = station["stationType"]  # GPO, DPO (district) or SPO (sub)
            apply_category(Categories.POST_OFFICE, item)
            yield item
