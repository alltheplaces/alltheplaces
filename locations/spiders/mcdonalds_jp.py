from typing import Any

import scrapy
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_WEEKDAY, OpeningHours
from locations.items import Feature


class McdonaldsJPSpider(scrapy.Spider):
    name = "mcdonalds_jp"
    item_attributes = {"brand_wikidata": "Q38076"}
    start_urls = (
        "https://map.mcdonalds.co.jp/api/poi?uuid=91b35ff7-e1ca-47b5-a0c0-377c41a6c3f2&bounds=-11.17840187371178%2C56.25%2C70.61261423801925%2C-146.25&_=1513674348668",
    )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        results = response.json()
        for data in results:
            properties = {
                "ref": data["id"],
                "addr_full": data["address"],
                "branch": data["name"].removesuffix("店"),
                "lat": data["latitude"],
                "lon": data["longitude"],
            }

            item = Feature(**properties)
            apply_category(Categories.FAST_FOOD, item)
            yield scrapy.Request(
                f"https://map.mcdonalds.co.jp/api/poi/{data['key']}",
                callback=self.parse_details,
                cb_kwargs={"item": item},
            )

    def parse_details(self, response: Response, item: Feature, **kwargs: Any) -> Any:
        details = response.json()
        item["phone"] = details["tel"]
        item["opening_hours"] = oh = OpeningHours()
        for days, key in [(DAYS_WEEKDAY, "平日"), (["Sa"], "土曜"), (["Su"], "休日")]:
            oh.add_days_range(days, details[f"営業時間_{key}_店_From"], details[f"営業時間_{key}_店_To"])
        yield item
