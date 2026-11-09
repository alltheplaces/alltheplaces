from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import clean_address


class BrandonHireGBSpider(JSONBlobSpider):
    name = "brandon_hire_gb"
    item_attributes = {"brand": "Brandon Hire Station", "brand_wikidata": "Q111578673"}
    start_urls = [
        "https://brandonhirestation.com/graphql?query=query+getStoreLocations%7BstoreLocations%7B...StoreLocationFragment+__typename%7D%7Dfragment+StoreLocationFragment+on+StoreLocation%7Bstore_id+location_id+store_name+address%7Bline_one+line_two+city+county+postcode+phone+email+__typename%7Dcoordinates%7Blat+long+__typename%7Dspecialist+short_description+popular_searches+opening_info+opening_hours%7Bmonday+tuesday+wednesday+thursday+friday+saturday+sunday+__typename%7Durl_key+...StoreLocationAvailabilityFragment+__typename%7Dfragment+StoreLocationAvailabilityFragment+on+StoreLocation%7Bavailability%7Benabled+__typename%7D__typename%7D&operationName=getStoreLocations&variables=%7B%7D"
    ]
    custom_settings = {"ROBOTSTXT_OBEY": False}
    locations_key = ["data", "storeLocations"]

    def pre_process_data(self, feature: dict) -> None:
        address = feature.get("address") or {}
        feature["street_address"] = clean_address([address.get("line_one"), address.get("line_two")])
        feature["phone"] = address.get("phone")
        feature["email"] = address.get("email")
        feature["city"] = address.get("city")
        feature["postcode"] = address.get("postcode")
        feature["website"] = "https://brandonhirestation.com/branch-finder/" + feature.get("url_key")
        feature.pop("address")

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name").removeprefix("Brandon Hire Station").strip()
        if feature.get("opening_hours"):
            item["opening_hours"] = OpeningHours()
            for day in DAYS_FULL:
                if "-" in feature["opening_hours"][day.lower()]:
                    open, close = feature["opening_hours"][day.lower()].split(" - ")
                    item["opening_hours"].add_range(day, open, close)
        apply_category(Categories.SHOP_TOOL_HIRE, item)
        yield item
