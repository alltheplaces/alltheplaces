from chompjs import parse_js_object
from scrapy.http import Request

from locations.geo import country_coordinates
from locations.hours import OpeningHours
from locations.json_blob_spider import JSONBlobSpider
from locations.spiders.sunglass_hut_1 import SUNGLASS_HUT_SHARED_ATTRIBUTES
from locations.user_agents import BROWSER_DEFAULT

SUNGLASS_HUT_3_COUNTRIES = {
    "BR": {"id": 17001},
    "DE": {"id": 14351},
    "ES": {"id": 13251},
    "FR": {"id": 13801},
    "MX": {"id": 16001},
}


class SunglassHut3Spider(JSONBlobSpider):
    name = "sunglass_hut_3"
    item_attributes = SUNGLASS_HUT_SHARED_ATTRIBUTES
    user_agent = BROWSER_DEFAULT
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def start_requests(self):
        country_coords = country_coordinates(return_lookup=True)
        for country in SUNGLASS_HUT_3_COUNTRIES:
            store_id = SUNGLASS_HUT_3_COUNTRIES[country]["id"]
            if coords := country_coords.get(country):
                yield Request(
                    url=f"https://www.sunglasshut.com/AjaxSGHFindPhysicalStoreLocations?latitude={coords[0]}&longitude={coords[1]}&radius=1000&storeId={store_id}",
                    callback=self.parse,
                )

    def extract_json(self, response):
        return parse_js_object(response.text)["locationDetails"]

    def pre_process_data(self, location):
        location["street_address"] = location.pop("address")

    def post_process_item(self, item, response, location):
        # Maybe this is interesting
        self.crawler.stats.inc_value(f"atp/{self.name}/store_type/{location['storeType']}")

        item["opening_hours"] = OpeningHours()
        for rule in location["hours"]:
            item["opening_hours"].add_range(rule["day"], rule["open"], rule["close"])
        yield item
