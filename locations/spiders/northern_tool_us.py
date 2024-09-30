from typing import override

from scrapy import FormRequest, Spider

from locations.dict_parser import DictParser
from locations.hours import DAYS_EN, DAYS_FULL, OpeningHours
from locations.user_agents import BROWSER_DEFAULT


class NorthernToolUSSpider(Spider):
    name = "northern_tool_us"
    item_attributes = {"brand": "Northern Tool + Equipment", "brand_wikidata": "Q43379813"}
    requires_proxy = True  # cloudflare
    user_agent = BROWSER_DEFAULT

    @override
    def start_requests(self):
        yield FormRequest(
            method="GET",
            url="https://www.northerntool.com/wcs/resources/store/6970/storelocator/latitude/38.8/longitude/-106.5",
            formdata={
                "resultFormat": "json",
                "siteLevelStoreSearch": "false",
                "radius": "5632",  # empirical maximum radius
                "maxItems": "1000",
            },
            callback=self.parse_storelocator,
        )

    def parse_storelocator(self, response):
        for store in response.json()["PhysicalStore"]:
            feature = DictParser.parse(store)
            feature["housenumber"] = store["addressLine"][0].split(" ")[0]
            feature["name"] = store["Description"][0]["displayStoreName"]
            feature["opening_hours"] = self.parse_opening_hours(store)
            feature["ref"] = store["uniqueID"]
            feature["state"] = store["stateOrProvinceName"]
            feature["street"] = " ".join(store["addressLine"][0].split(" ")[1:])
            feature["street_address"] = None  # build this during address cleanup
            feature["website"] = f'https://www.northerntool.com/store/{store["x_url"]}/'
            yield feature

    @staticmethod
    def parse_opening_hours(store):
        hours = OpeningHours()
        for attr in store["Attribute"]:
            if attr["name"].title() in DAYS_FULL:  # only want the attr['name'] that are all-caps weekday names
                day = DAYS_EN[attr["name"].title()]  # map it to the OSM-like form of the weekday name (e.g. "Mo")
                time_open, time_close = attr["value"].split("_")  # if addr['value'] looks like '0700_1900' ...
                time_open = time_open[:2] + ":" + time_open[2:]  # ... this now looks like 07:00
                time_close = time_close[:2] + ":" + time_close[2:]  # ... this now looks like 19:00
                hours.add_range(day, time_open, time_close)
        return hours
