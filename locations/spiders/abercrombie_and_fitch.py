from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_FROM_SUNDAY, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider

BRANDS = {
    "ACF": ("Abercrombie & Fitch", "Q319344"),
    "KID": ("Abercrombie Kids", "Q429856"),
}


class AbercrombieAndFitchSpider(JSONBlobSpider):
    name = "abercrombie_and_fitch"
    allowed_domains = ["abercrombie.com"]
    start_urls = ["https://www.abercrombie.com/api/ecomm/a-us/storelocator/search?country="]
    locations_key = "physicalStores"
    # robots.txt disallows /api/*, which is the only path serving store data.
    custom_settings = {"ROBOTSTXT_OBEY": False}
    requires_proxy = True

    def pre_process_data(self, location: dict) -> None:
        location["street_address"] = location.pop("addressLine")[0]
        if (state := location.pop("stateOrProvinceName")) != location["country"]:
            location["state"] = state
        if location.get("postalCode") == "-":
            location.pop("postalCode")

    def post_process_item(self, item: Feature, response: Response, location: dict) -> Iterable[Feature]:
        attributes = {
            attribute["name"]: attribute["value"]
            for attribute in location["physicalStoreAttribute"]
            if attribute["Displayable"]
        }
        # Inventory-only records expose no displayable attributes, brand included.
        if not (brand := BRANDS.get(attributes.get("Brand"))):
            return
        item["brand"], item["brand_wikidata"] = brand
        item["branch"] = item.pop("name")

        if hours := attributes.get("hours-Week1"):
            item["opening_hours"] = OpeningHours()
            for day, times in zip(DAYS_FROM_SUNDAY, hours.split(",")):
                open_time, _, close_time = times.partition("|")
                if open_time == close_time:
                    item["opening_hours"].set_closed(day)
                else:
                    item["opening_hours"].add_range(day, open_time, close_time)

        apply_category(Categories.SHOP_CLOTHES, item)
        yield item
