from locations.categories import Categories
from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class FairpriceSGSpider(JSONBlobSpider):
    name = "fairprice_sg"
    item_attributes = {
        "brand": "NTUC Fairprice",
        "brand_wikidata": "Q6955519",
        "extras": Categories.SHOP_SUPERMARKET.value,
    }
    start_urls = ["https://public-api.omni.fairprice.com.sg/stores"]

    def extract_json(self, response):
        return response.json()["data"]["fpstores"]

    def post_process_item(self, item, response, location):
        if location.get("storeType") == "Click and Collect":
            # Skip Click and Collect locations as they are not mentioned in store locator map
            yield None
        else:
            item["branch"] = item.pop("name")
            item["name"] = location.get("storeType")
            item["street_address"] = None
            self.parse_hours(item, location)
            yield item

    def parse_hours(self, item: Feature, location: dict):
        if location.get("is24Hour"):
            item["opening_hours"] = "24/7"
            return
        elif location.get("sngBusinessHours", {}).get("Valid") == False:
            # Store works daily
            oh = OpeningHours()
            oh.add_days_range(DAYS, location.get("fromTime"), location.get("toTime"), time_format="%H:%M:%S")
            item["opening_hours"] = oh
            return
        elif location.get("sngBusinessHours", {}).get("Valid") == True:
            # Only 17 stores have this format, it's not worth to implement
            return
