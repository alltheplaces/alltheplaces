from typing import Iterable

import scrapy
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature


class CuraleafUSSpider(scrapy.Spider):
    name = "curaleaf_us"
    item_attributes = {"brand": "Curaleaf", "brand_wikidata": "Q85754829"}
    allowed_domains = ["curaleaf.com"]
    start_urls = ["https://curaleaf.com/api/dispensaries?limit=100&page=1"]

    def parse(self, response: Response, **kwargs) -> Iterable:
        data = response.json()
        for doc in data.get("docs", []):
            yield from self.parse_doc(doc)

        total_pages = data.get("totalPages", 1)
        current_page = data.get("page", 1)
        if current_page < total_pages:
            next_page = current_page + 1
            yield scrapy.Request(
                f"https://curaleaf.com/api/dispensaries?limit=100&page={next_page}",
                callback=self.parse,
            )

    def parse_doc(self, doc: dict) -> Iterable[Feature]:
        loc = doc.get("synced_location_information", {})
        coordinate = loc.get("coordinate", [])

        item = Feature()
        item["ref"] = doc.get("unique_id") or doc.get("slug")
        item["branch"] = doc.get("friendly_name")
        item["street_address"] = loc.get("address")
        item["city"] = loc.get("city")
        item["state"] = (doc.get("state") or {}).get("abbreviation")
        item["postcode"] = loc.get("zipcode")
        item["country"] = loc.get("country")
        item["phone"] = loc.get("phone")
        item["website"] = f"https://curaleaf.com/dispensary/{doc['slug']}"

        if len(coordinate) == 2:
            item["lon"] = coordinate[0]
            item["lat"] = coordinate[1]

        times = loc.get("times", {})
        if times:
            oh = OpeningHours()
            day_map = {
                "sundayTimes": "Sunday",
                "mondayTimes": "Monday",
                "tuesdayTimes": "Tuesday",
                "wednesdayTimes": "Wednesday",
                "thursdayTimes": "Thursday",
                "fridayTimes": "Friday",
                "saturdayTimes": "Saturday",
            }
            for key, day_name in day_map.items():
                for time_range in times.get(key, []):
                    oh.add_range(day_name, time_range[0], time_range[1], "%H:%M")
            item["opening_hours"] = oh

        apply_category(Categories.SHOP_CANNABIS, item)
        yield item
