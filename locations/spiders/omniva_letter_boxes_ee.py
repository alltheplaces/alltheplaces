import re
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS, DAYS_EE, sanitise_day
from locations.items import Feature


class OmnivaLetterBoxesEESpider(Spider):
    """Street letter boxes from the omniva.ee locations map. The omniva spider covers parcel machines and post offices."""

    name = "omniva_letter_boxes_ee"
    item_attributes = {"operator": "Omniva", "operator_wikidata": "Q282457"}
    allowed_domains = ["www.omniva.ee"]
    # The map loads every point type at once; letter boxes are only listed for Estonia.
    start_urls = ["https://www.omniva.ee/wp-json/custom/v1/omniva-map-data?lang=et"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for box in response.json()["letter_boxes"]:
            item = Feature()
            # Titles look like "Kirjakast 1-106"; the number is shown on the box.
            item["ref"] = box["title"].removeprefix("Kirjakast").strip() or box["id"]
            item["lat"], item["lon"] = box["lat"], box["lng"]
            # "ZIP" is a six-digit Omniva point code (Estonian postcodes have five digits), which the address repeats.
            item["addr_full"] = box["address_text"].removesuffix(box["ZIP"]).strip(" ,")
            item["extras"]["ref:omniva"] = box["id"]
            if collection_times := self.parse_collection_times(box["SERVICE_HOURS"]):
                item["extras"]["collection_times"] = collection_times
            apply_category(Categories.POST_BOX, item)
            yield item

    @classmethod
    def parse_collection_times(cls, service_hours: str) -> str | None:
        # e.g. "Tühjendamine:;T,N,R 08:00" (emptying: Tuesday, Thursday, Friday at 08:00)
        rules = []
        for days, time in re.findall(r"([EKLNPRT](?:\s*,\s*[EKLNPRT])*)\s+(\d{1,2}:\d{2})", service_hours):
            day_list = [sanitise_day(d, DAYS_EE) for d in days.split(",")]
            rules.append(f"{cls.join_days(day_list)} {time.zfill(5)}")
        return "; ".join(rules) or None

    @staticmethod
    def join_days(days: list[str]) -> str:
        # Collapse runs of three or more consecutive days into a range, e.g. Tu,We,Th,Fr -> Tu-Fr.
        indexes = [DAYS.index(d) for d in days]
        groups, start = [], 0
        for i in range(1, len(indexes) + 1):
            if i == len(indexes) or indexes[i] != indexes[i - 1] + 1:
                run = days[start:i]
                groups.append(f"{run[0]}-{run[-1]}" if len(run) >= 3 else ",".join(run))
                start = i
        return ",".join(groups)
