from scrapy import FormRequest, Spider

from locations.dict_parser import DictParser
from locations.hours import DAYS_EN, DAYS_FULL, OpeningHours
from locations.user_agents import BROWSER_DEFAULT


class NorthernToolUSSpider(Spider):
    name = "northern_tool_us"
    item_attributes = {"brand": "Northern Tool + Equipment", "brand_wikidata": "Q43379813"}
    requires_proxy = True  # cloudflare
    user_agent = BROWSER_DEFAULT

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
            callback=NorthernToolUSSpider.handle_response,
        )

    @staticmethod
    def handle_response(response):
        for store in response.json()["PhysicalStore"]:
            feature = DictParser.parse(store)
            feature["name"] = store["Description"][0]["displayStoreName"]
            feature["opening_hours"] = OpeningHours()
            feature["ref"] = store["uniqueID"]
            feature["state"] = store["stateOrProvinceName"]
            feature["street_address"] = store["addressLine"][0]
            feature["website"] = f'https://www.northerntool.com/store/{store["x_url"]}/'
            for attr in store["Attribute"]:
                if attr["name"].title() in DAYS_FULL:
                    feature["opening_hours"].add_range(
                        DAYS_EN[attr["name"].title()],
                        attr["value"][0:2] + ":" + attr["value"][2:4],
                        attr["value"][5:7] + ":" + attr["value"][7:9],
                    )
            yield feature
