import html

from scrapy import Spider

from locations.dict_parser import DictParser
from locations.hours import OpeningHours, sanitise_day
from locations.user_agents import BROWSER_DEFAULT


class MaxAndCompanySpider(Spider):
    name = "max_and_company"
    item_attributes = {"brand": "MAX&Co.", "brand_wikidata": "Q120570926"}
    start_urls = [
        "https://gb.maxandco.com/store-locator?south=-90&west=-180&north=90&east=180&listJson=true&withoutRadius=false"
    ]
    no_refs = True
    user_agent = BROWSER_DEFAULT

    def parse(self, response, **kwargs):
        for location in response.json()["features"]:
            if location["properties"]["storeHidden"]:
                continue

            item = DictParser.parse(location["properties"])
            item["geometry"] = location["geometry"]
            item["name"] = html.unescape(location["properties"]["displayName"])
            item["phone"] = "; ".join(
                filter(None, [location["properties"]["phone1"], location["properties"]["phone2"]])
            )
            item["addr_full"] = location["properties"]["formattedAddress"]
            item["state"] = location["properties"]["prov"]

            item["opening_hours"] = OpeningHours()
            for day, times in location["properties"]["openingHours"].items():
                if day := sanitise_day(day):
                    for time in times:
                        start_time, end_time = time.split(" - ")
                        if end_time == "24.00":
                            end_time = "23.59"
                        item["opening_hours"].add_range(day, start_time, end_time, time_format="%H.%M")

            yield item
