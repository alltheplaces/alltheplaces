from typing import Iterable

from scrapy.http import Response

from locations.hours import DAYS_SE, OpeningHours, sanitise_day
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class HemkopSESpider(JSONBlobSpider):
    name = "hemkop_se"
    item_attributes = {"brand": "Hemköp", "brand_wikidata": "Q10521746"}
    start_urls = ["https://www.hemkop.se/axfood/rest/store"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if not item["street_address"]:  # Not enough location data
            return
        item["branch"] = (item.pop("name", "") or "").removeprefix("Hemköp ")
        item["phone"] = feature["address"].get("phone")
        item["website"] = "https://www.hemkop.se/butik/{}".format(item["ref"])

        try:
            item["opening_hours"] = OpeningHours()
            for rule in feature["openingHours"]:
                day, times = rule.split(" ")
                start_time, end_time = times.split("-")
                if day := sanitise_day(day, DAYS_SE):
                    item["opening_hours"].add_range(day, start_time, end_time)
        except:
            pass

        yield item
