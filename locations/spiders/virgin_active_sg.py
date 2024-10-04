from chompjs import parse_js_object
from scrapy.http import JsonRequest

from locations.hours import OpeningHours
from locations.json_blob_spider import JSONBlobSpider
from locations.spiders.virgin_active_bw_na_za import VIRGIN_ACTIVE_SHARED_ATTRIBUTES


class VirginActiveSGSpider(JSONBlobSpider):
    name = "virgin_active_sg"
    item_attributes = VIRGIN_ACTIVE_SHARED_ATTRIBUTES
    start_urls = ["https://www.virginactive.com.sg/locations"]

    def extract_json(self, response):
        json_data = parse_js_object(response.xpath('//script[@id="__NEXT_DATA__"]/text()').get())
        return json_data["props"]["pageProps"]["clubGroups"][0]["clubs"]

    def post_process_item(self, item, response, location):
        yield JsonRequest(
            url="https://www.virginactive.com.sg/" + location["path"], meta={"item": item}, callback=self.parse_location
        )

    def parse_location(self, response):
        item = response.meta["item"]
        location = parse_js_object(response.xpath('//script[@id="__NEXT_DATA__"]/text()').get())["props"]["pageProps"]
        item["website"] = response.url
        item["email"] = location["email"]
        item["opening_hours"] = OpeningHours()
        for day in location["openingHours"]:
            item["opening_hours"].add_ranges_from_string(day["label"] + " " + day["value"])
        yield item
