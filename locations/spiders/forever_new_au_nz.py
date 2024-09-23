import json

from scrapy.http import JsonRequest

from locations.hours import OpeningHours
from locations.json_blob_spider import JSONBlobSpider

FOREVER_NEW_SHARED_ATTRIBUTES = {"brand": "Forever New", "brand_wikidata": "Q119221929"}


class ForeverNewAUNZSpider(JSONBlobSpider):
    name = "forever_new_au_nz"
    item_attributes = FOREVER_NEW_SHARED_ATTRIBUTES
    start_urls = [
        "https://www.forevernew.com.au/locator/index/search/?longitude=0&latitude=0&radius=100000&type=all",
        "https://www.forevernew.co.nz/locator/index/search/?longitude=0&latitude=0&radius=100000&type=all",
    ]
    custom_settings = {"ROBOTSTXT_OBEY": False}
    locations_key = ["results", "results"]

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def post_process_item(self, item, response, location):
        # Ignore locations which are embedded within a Myer department store.
        if location.get("name") is not None and " MYER " in location["name"].upper():
            return
        hours = json.loads(location["trading_hours"])
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(str(hours))
        yield item
