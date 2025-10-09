from locations.categories import Extras, apply_yes_no
from locations.hours import DAYS_WEEKDAY, DAYS_WEEKEND, OpeningHours
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
        weekday_open, weekday_close = feature["workingHours"].split("-")
        oh.add_days_range(DAYS_WEEKDAY, weekday_open, weekday_close)
        weekend_open, weekend_close = feature["workingHoursWeekend"].split("-")
        oh.add_days_range(DAYS_WEEKEND, weekend_open, weekend_close)
        item["opening_hours"] = oh

        yield item
