from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature

DAY_NAMES = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]


class BelpostBYSpider(Spider):
    name = "belpost_by"
    item_attributes = {"operator": "Белпошта", "operator_wikidata": "Q2662336"}
    allowed_domains = ["api.belpost.by"]
    # One map-extent search returns every post office or letter box in the country. The extent must stay
    # inside Belarus (the API rejects latitudes above 56.198673 or longitudes below 23.131879).
    EXTENT = "map=true&top_longitude=23.14&top_latitude=56.19&bottom_longitude=32.77&bottom_latitude=51.27"
    custom_settings = {"DOWNLOAD_TIMEOUT": 120}

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(f"https://api.belpost.by/api/v1/ops?{self.EXTENT}", callback=self.parse_offices)
        yield JsonRequest(f"https://api.belpost.by/api/v1/ops-boxes?{self.EXTENT}", callback=self.parse_boxes)

    def parse_offices(self, response: Response, **kwargs: Any) -> Any:
        for office in response.json():
            item = Feature()
            item["ref"] = str(office["id"])
            item["branch"] = office["name"]
            item["lat"], item["lon"] = office["latitude"], office["longitude"]
            item["postcode"] = office["postcode"]
            item["city"] = office["city"]
            item["street"] = office["street"]
            item["housenumber"] = office["house"]
            item["addr_full"] = office["address"]
            item["phone"] = office["phone"]
            item["opening_hours"] = self.parse_timetable(office.get("timetable") or [])
            apply_category(Categories.POST_OFFICE, item)
            yield item

    def parse_boxes(self, response: Response, **kwargs: Any) -> Any:
        for box in response.json():
            item = Feature()
            item["ref"] = str(box["id"])
            item["lat"], item["lon"] = box["latitude"], box["longitude"]
            item["city"] = box["city"]
            item["street"] = box["street"]
            item["housenumber"] = box["house"]
            item["addr_full"] = box["address"]
            # The post office that empties the box.
            if box.get("info"):
                item["extras"]["note"] = box["info"]
            apply_category(Categories.POST_BOX, item)
            yield item

    @staticmethod
    def parse_timetable(rules: list[dict]) -> OpeningHours:
        # Rules are a day ("monday") or a day range ("tuesday_friday"), each with an optional lunch break.
        oh = OpeningHours()
        for rule in rules:
            names = rule["type"].split("_")
            if not rule.get("from") or not rule.get("to") or not all(n in DAY_NAMES for n in names):
                continue
            first, last = DAY_NAMES.index(names[0]), DAY_NAMES.index(names[-1])
            for day in DAYS[first : last + 1]:
                if rule.get("lunch_from") and rule.get("lunch_to"):
                    oh.add_range(day, rule["from"], rule["lunch_from"])
                    oh.add_range(day, rule["lunch_to"], rule["to"])
                else:
                    oh.add_range(day, rule["from"], rule["to"])
        return oh
