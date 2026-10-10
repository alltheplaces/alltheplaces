import re
from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.hours import sanitise_day
from locations.items import Feature


class LatvijasPastsLetterBoxesLVSpider(Spider):
    """Street letter boxes ("vēstuļu kastītes") from the mans.pasts.lv map. The latvijas_pasts spider covers post
    offices and parcel lockers from the same API."""

    name = "latvijas_pasts_letter_boxes_lv"
    item_attributes = {"operator": "Latvijas Pasts", "operator_wikidata": "Q1807088"}
    allowed_domains = ["mans.pasts.lv"]

    async def start(self) -> AsyncIterator[JsonRequest]:
        # Service location type 9 is a letter box; there are about 530, so one page holds them all.
        yield JsonRequest(
            "https://mans.pasts.lv/api/public/addresses/service_location?type[]=9&search=&itemsPerPage=1500&page=1"
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for box in response.json():
            item = Feature()
            # Labels look like "Ķekava vēstuļu kastīte Nr.LVP257"; the number is unique.
            if number := re.search(r"Nr\.\s*(\S+)$", box["label"]):
                item["ref"] = number.group(1)
            else:
                item["ref"] = box["id"]
            item["extras"]["ref:latvijas_pasts"] = box["id"]
            item["lat"], item["lon"] = box["latitude"], box["longitude"]
            item["addr_full"] = box["readableAddress"]
            item["postcode"] = box["postCode"]
            # Where the box is, e.g. "Pie pasta nodaļas" (at the post office) or "Pakomāts" (at a parcel locker).
            if info := box.get("info"):
                item["extras"]["description"] = info
            times = []
            for key, time in (box.get("pickUpTimes") or {}).items():
                if key == "@type":
                    continue
                # Only "workdays" is used at the time of writing; other keys are day names ("saturday").
                days = "Mo-Fr" if key == "workdays" else sanitise_day(key)
                if not days:
                    self.logger.warning("Unknown pick-up day %s for box %s", key, box["id"])
                elif re.fullmatch(r"\d{2}:\d{2}", time or ""):
                    times.append(f"{days} {time}")
            if times:
                item["extras"]["collection_times"] = "; ".join(times)
            apply_category(Categories.POST_BOX, item)
            yield item
