from scrapy import Spider

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.spiders.sunglass_hut_1 import SunglassHut1Spider
from locations.user_agents import BROWSER_DEFAULT


class SunglassHutGBSpider(Spider):
    name = "sunglass_hut_gb"
    item_attributes = SunglassHut1Spider.item_attributes
    start_urls = [
        "https://www.sunglasshut.com/AjaxSGHFindPhysicalStoreLocations?latitude=53.4138458&longitude=-1.782017&radius=1000&storeId=11352"
    ]
    user_agent = BROWSER_DEFAULT

    def parse(self, response, **kwargs):
        for location in response.json()["locationDetails"]:
            if location.get("storeStatus") != "OPEN":
                continue
            location["street_address"] = location.pop("address")
            item = DictParser.parse(location)

            item["opening_hours"] = OpeningHours()
            for rule in location["hours"]:
                item["opening_hours"].add_range(rule["day"], rule["open"], rule["close"])

            yield item
