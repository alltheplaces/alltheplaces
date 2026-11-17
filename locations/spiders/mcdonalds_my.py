from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.spiders.mcdonalds import McdonaldsSpider


class McdonaldsMYSpider(JSONBlobSpider):
    name = "mcdonalds_my"
    item_attributes = McdonaldsSpider.item_attributes
    start_urls = [
        "https://www.mcdonalds.com.my/locate-us/stores?distance=100000&lat=&lng=&state=&category=&address=&is_suggestion=0&is_locate=0"
    ]
    locations_key = "stores"

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["branch"] = item["ref"] = item.pop("name").removeprefix("McDonlad's ")

        services = [c["cat_name"] for c in feature["cat"]]

        if "McCafe" in services:
            mccafe = item.deepcopy()
            mccafe["ref"] = "{}_mccafe".format(item["ref"])
            mccafe["brand"] = "McCafé"
            mccafe["brand_wikidata"] = "Q3114287"
            apply_category(Categories.CAFE, mccafe)
            yield mccafe

        item["opening_hours"] = "24/7" if "24 Hours" in services else None
        apply_yes_no(Extras.BREAKFAST, item, "Breakfast" in services)
        apply_yes_no(Extras.SELF_CHECKOUT, item, "Digital Order Kiosk" in services)
        apply_yes_no(Extras.DRIVE_THROUGH, item, "Drive-Thru" in services)
        apply_yes_no(Extras.DRIVE_THROUGH, item, "McDelivery" in services)
        apply_yes_no(Extras.WIFI, item, "WiFi" in services)
        apply_category(Categories.FAST_FOOD, item)
        yield item
