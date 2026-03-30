from typing import Iterable

from scrapy.http import TextResponse

from locations.hours import OpeningHours, day_range, sanitise_day
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines


class CardsDirectGBSpider(JSONBlobSpider):
    name = "cards_direct_gb"
    item_attributes = {"brand": "Cards Direct", "brand_wikidata": "Q114826765"}
    start_urls = ["https://www.cardsdirect.co.uk/storefinder/index/loadstore/?websiteIds[]=1"]
    locations_key = "stores"
    drop_attributes = {"facebook", "twitter"}

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name").replace("Cards Direct ", "")
        item["street_address"] = merge_address_lines([feature["address_line_1"], feature["address_line_2"]])
        item["opening_hours"] = OpeningHours()
        for days in feature["opening_times"]["regular"]:
            if " - " in days["name"]:
                start_day, end_day = days["name"].split(" - ")
            else:
                start_day = end_day = days["name"]
            start_day = sanitise_day(start_day)
            end_day = sanitise_day(end_day)
            if start_day and end_day:
                item["opening_hours"].add_days_range(
                    day_range(start_day, end_day), days["time_open"], days["time_close"]
                )
        yield item
