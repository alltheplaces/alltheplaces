from chompjs import parse_js_object

from locations.hours import DAYS_FULL, OpeningHours
from locations.json_blob_spider import JSONBlobSpider
from locations.spiders.paul_fr import PAUL_SHARED_ATTRIBUTES


class PaulArabiaSpider(JSONBlobSpider):
    name = "paul_arabia"
    item_attributes = PAUL_SHARED_ATTRIBUTES
    start_urls = ["https://www.paularabia.com/Site/GetMarkers"]

    def extract_json(self, response):
        return parse_js_object(response.json()["markers"])

    def post_process_item(self, item, response, location):
        item["street_address"] = item.pop("addr_full")
        item["opening_hours"] = OpeningHours()
        for day in DAYS_FULL:
            item["opening_hours"].add_ranges_from_string(day + " " + location[f"{day}Hours"])
        yield item
