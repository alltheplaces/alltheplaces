import chompjs

from locations.hours import DAYS, OpeningHours
from locations.json_blob_spider import JSONBlobSpider


class JackWillsGBSpider(JSONBlobSpider):
    name = "jack_wills_gb"
    item_attributes = {
        "brand": "Jack Wills",
        "brand_wikidata": "Q6115814",
    }
    start_urls = [
        "https://www.jackwills.com/stores/search?countryName=United%20Kingdom&countryCode=GB&lat=0&long=0&sd=40"
    ]
    custom_settings = {
        "ROBOTSTXT_OBEY": False,
    }
    requires_proxy = True

    def extract_json(self, response):
        return chompjs.parse_js_object(response.xpath('//script[contains(text(),"var stores = ")]/text()').get())

    def post_process_item(self, item, response, location):
        item["ref"] = location["code"]
        item["website"] = "https://www.jackwills.com/" + location["storeUrl"]
        item["opening_hours"] = OpeningHours()
        for rule in location["openingTimes"]:
            item["opening_hours"].add_range(DAYS[rule["dayOfWeek"]], rule["openingTime"], rule["closingTime"])
        yield item
