import json
from typing import Iterable

from scrapy.http import Request, TextResponse

from locations.categories import Categories, apply_category
from locations.hours import DAYS_NL, OpeningHours, sanitise_day
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class JbcSpider(JSONBlobSpider):
    name = "jbc"
    item_attributes = {"brand": "JBC", "brand_wikidata": "Q2671470"}
    start_urls = [
        "https://www.jbc.be/on/demandware.store/Sites-JBC-Webshop-BE-Site/nl_BE/Stores-FindStores?lat=50.85&long=4.35&radius=1000&limit=1000"
    ]
    needs_json_request = True
    locations_key = "stores"
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Request]:
        item["branch"] = item.pop("name").removeprefix("JBC ").title()
        item.pop("street_address", None)
        item.pop("email", None)  # Generic head office / customer care addresses, not per store
        item["street"] = feature["address1"]
        item["housenumber"] = feature["address2"]
        if post_box := feature.get("postBox"):
            item["housenumber"] += post_box if post_box.startswith("-") else "/" + post_box
        item["extras"]["website:nl"] = feature["detailURL"]
        item["extras"]["website:fr"] = feature["detailURL"].replace("/nl-be/winkels/", "/fr-be/magasins/")
        # French is the more natural language for Luxembourg
        item["website"] = item["extras"]["website:fr" if item["country"] == "LU" else "website:nl"]
        yield response.follow(feature["detailURL"], callback=self.parse_hours, cb_kwargs={"item": item})

    def parse_hours(self, response: TextResponse, item: Feature) -> Iterable[Feature]:
        item["opening_hours"] = OpeningHours()
        for day in response.xpath('//li[contains(@class, "store-opening-hours__listitem")][@data-hours]'):
            day_name = sanitise_day(
                day.xpath('.//span[contains(@class, "store-opening-hours__listitem__weekday ")]/text()')
                .get("")
                .strip(),
                DAYS_NL,
            )
            if not day_name:
                continue
            # The list covers the coming 7 days; skip exceptional openings/closings so only regular hours are kept
            if "is-special-day" in day.xpath("@class").get("").split():
                continue
            if hours := json.loads(day.xpath("@data-hours").get()):
                for times in hours:
                    item["opening_hours"].add_range(day_name, times["open"], times["close"])
            else:
                item["opening_hours"].set_closed(day_name)
        apply_category(Categories.SHOP_CLOTHES, item)
        yield item
