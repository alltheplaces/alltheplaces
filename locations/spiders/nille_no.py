from typing import Any, Iterable
from urllib.parse import urljoin

from scrapy import Spider
from scrapy.http import TextResponse

from locations.dict_parser import DictParser
from locations.hours import DAYS_FROM_SUNDAY, OpeningHours
from locations.items import Feature


class NilleNOSpider(Spider):
    name = "nille_no"
    item_attributes = {"brand": "Nille", "brand_wikidata": "Q11991429"}
    start_urls = ["https://www.nille.no/api/store-list/by-query?query="]
    custom_settings = {"DEFAULT_REQUEST_HEADERS": {"Accept": "application/json"}}

    def parse(self, response: TextResponse, **kwargs: Any) -> Iterable[Feature]:
        for location in response.json().get("stores", []):
            if location.get("permanentlyClosed") or location.get("temporarilyClosed"):
                continue
            item = DictParser.parse(location)

            item["branch"] = item.pop("name").removeprefix("Nille").strip()

            item["street_address"] = item.pop("street")

            if url := location.get("url"):
                item["website"] = urljoin("https://www.nille.no", url)

            if main_image := location.get("mainImage"):
                if isinstance(main_image, dict) and not main_image.get("isFallbackImage"):
                    if src := main_image.get("src"):
                        item["image"] = urljoin("https://www.nille.no", src)

            if location_hours := location.get("workingHours"):
                opening_hours = OpeningHours()
                for day_hours in location_hours:
                    day_index = day_hours.get("weekDay")
                    if day_index is None:
                        continue

                    day = DAYS_FROM_SUNDAY[day_index]
                    if day_hours.get("closed"):
                        opening_hours.set_closed(day)
                        continue

                    opening_hours.add_range(day, day_hours.get("startTime"), day_hours.get("endTime"))
                if opening_hours:
                    item["opening_hours"] = opening_hours

            yield item
