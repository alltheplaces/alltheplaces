from typing import Iterable

from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class MainEventSpider(JSONBlobSpider):
    name = "main_event"
    item_attributes = {"brand": "Main Event", "brand_wikidata": "Q56062981"}
    start_urls = ["https://www.mainevent.com/content/mainevent/servletresource.locationSearch.json"]
    locations_key = "centers"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[JsonRequest]:
        if not feature["enabled"]:
            return
        item["ref"] = feature["centerId"]
        item["branch"] = feature["centerName"]
        item["street_address"] = item.pop("addr_full")
        apply_category(Categories.AMUSEMENT_ARCADE, item)
        yield JsonRequest(
            f"https://www.mainevent.com/content/mainevent/servletresource.locationHours.json?centerId={feature['centerId']}",
            callback=self.parse_hours,
            cb_kwargs={"item": item},
        )

    def parse_hours(self, response: Response, item: Feature) -> Iterable[Feature]:
        item["opening_hours"] = OpeningHours()
        for day, rule in response.json().items():
            if rule["isClosedWholeDay"]:
                item["opening_hours"].set_closed(day)
                continue
            for interval in rule["openIntervals"]:
                item["opening_hours"].add_range(day, interval["start"], interval["end"])
        yield item
