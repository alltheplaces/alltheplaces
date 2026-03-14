import chompjs

from locations.hours import OpeningHours
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines


class AwaySpider(JSONBlobSpider):
    name = "away"
    item_attributes = {"brand": "Away", "brand_wikidata": "Q48743138"}
    start_urls = ["https://www.awaytravel.com/pages/stores"]

    def extract_json(self, response):
        search = "window.AwayStores ="
        script = response.xpath(f"//script[contains(text(), {search!r})]/text()").get()
        return chompjs.parse_js_object(script[script.find(search) + len(search) :])["stores"]

    def post_process_item(self, item, response, location):
        item["branch"] = item.pop("name")

        item["addr_full"] = merge_address_lines(location["address"])
        item["lon"], item["lat"] = location["coords"]

        oh = OpeningHours()
        for line in location["hours"]:
            oh.add_ranges_from_string(line)
        item["opening_hours"] = oh

        yield item
