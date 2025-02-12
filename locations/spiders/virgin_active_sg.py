from chompjs import parse_js_object
from scrapy.http import JsonRequest

from locations.hours import DAYS_3_LETTERS, OpeningHours
from locations.json_blob_spider import JSONBlobSpider
from locations.spiders.virgin_active_bw_na_za import VIRGIN_ACTIVE_SHARED_ATTRIBUTES


# Also used by virgin_active_au
class VirginActiveSGSpider(JSONBlobSpider):
    name = "virgin_active_sg"
    item_attributes = VIRGIN_ACTIVE_SHARED_ATTRIBUTES
    start_urls = ["https://www.virginactive.com.sg/locations"]

    def parse(self, response):
        json_data = parse_js_object(response.xpath('//script[@id="__NEXT_DATA__"]/text()').get())
        club_groups = json_data["props"]["pageProps"]["clubGroups"]
        for group in club_groups:
            features = group["clubs"]
            yield from self.parse_feature_array(response, features) or []

    def post_process_item(self, item, response, location):
        yield JsonRequest(
            url=response.url.replace("/locations", "") + location["path"],
            meta={"item": item},
            callback=self.parse_location,
        )

    def parse_location(self, response):
        item = response.meta["item"]
        location = parse_js_object(response.xpath('//script[@id="__NEXT_DATA__"]/text()').get())["props"]["pageProps"]
        item["website"] = response.url
        item["email"] = location["email"]
        item["branch"] = item.pop("name")
        item["opening_hours"] = OpeningHours()
        for day in location["openingHours"]:
            if day["value"].lower() == "closed" and day["label"] in DAYS_3_LETTERS:
                item["opening_hours"].set_closed(day["label"])
            else:
                item["opening_hours"].add_ranges_from_string(day["label"] + " " + day["value"])
        yield item
