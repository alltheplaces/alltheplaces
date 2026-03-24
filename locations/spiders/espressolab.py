from locations.categories import Extras, apply_yes_no
from locations.hours import DAYS_FULL, OpeningHours
from locations.json_blob_spider import JSONBlobSpider


class EspressolabSpider(JSONBlobSpider):
    name = "espressolab"
    item_attributes = {"brand": "Espressolab", "brand_wikidata": "Q97599059"}
    start_urls = ["https://espressolab.com/api/stores"]
    locations_key = "response"

    def post_process_item(self, item, response, feature):
        item["branch"] = item.pop("name")
        apply_yes_no(Extras.DELIVERY, item, feature["hasHomeDelivery"])
        apply_yes_no(Extras.WIFI, item, feature["hasWifi"])

        oh = OpeningHours()
        opening_data = feature.get("storeWorkTimes")
        for days_range in opening_data:
            if not days_range.get("isClosed"):
                oh.add_range(DAYS_FULL[days_range["dayNumber"] - 1], days_range["openTime"], days_range["closeTime"])
        item["opening_hours"] = oh

        yield item
