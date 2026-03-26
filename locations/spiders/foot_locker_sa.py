from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class FootLockerSASpider(JSONBlobSpider):
    name = "foot_locker_sa"
    item_attributes = {
        "brand": "Foot Locker",
        "brand_wikidata": "Q63335",
    }
    allowed_domains = ["www.footlocker.com.sa"]
    start_urls = [
        "https://www.footlocker.com.sa/rest/sau_en/V1/storeLocator/search?searchCriteria%5Bfilter_groups%5D%5B0%5D%5Bfilters%5D%5B0%5D%5Bfield%5D=status&searchCriteria%5Bfilter_groups%5D%5B0%5D%5Bfilters%5D%5B0%5D%5Bvalue%5D=1"
    ]
    locations_key = "items"
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        item["ref"] = feature["store_code"]
        for address_field in feature["address"]:
            if address_field["code"] == "street":
                item["addr_full"] = address_field["value"]
                break
        item["opening_hours"] = OpeningHours()
        hours_text = " ".join([f'{day_hours["label"]}: {day_hours["value"]}' for day_hours in feature["store_hours"]])
        item["opening_hours"].add_ranges_from_string(hours_text)
        apply_category(Categories.SHOP_SHOES, item)
        yield item
