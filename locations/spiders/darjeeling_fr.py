from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, Clothes, apply_category, apply_clothes
from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class DarjeelingFRSpider(JSONBlobSpider):
    name = "darjeeling_fr"
    item_attributes = {"brand": "Darjeeling", "brand_wikidata": "Q3016203"}
    start_urls = ["https://cdn.new.darjeeling.fr/yext/stores.json"]
    locations_key = "stores"

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        apply_category(Categories.SHOP_CLOTHES, item)
        apply_clothes(Clothes.UNDERWEAR, item)

        name = item.pop("name", "") or ""
        item["branch"] = name.removeprefix("Darjeeling").removeprefix(" ")
        try:
            if hours := feature.get("hours"):
                item["opening_hours"] = self.parse_hours(hours)
        except Exception:
            pass
        yield item

    @staticmethod
    def parse_hours(hours: dict) -> OpeningHours:
        oh = OpeningHours()
        for day in map(str.lower, DAYS_FULL):
            if hours[day].get("isClosed") is True:
                oh.set_closed(day)
            else:
                for time in hours[day]["openIntervals"]:
                    oh.add_range(day, time["start"], time["end"])
        return oh
