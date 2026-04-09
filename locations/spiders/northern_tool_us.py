import scrapy

from locations.dict_parser import DictParser
from locations.user_agents import FIREFOX_LATEST


class NorthernToolUSSpider(scrapy.Spider):
    name = "northern_tool_us"
    item_attributes = {"brand": "Northern Tool + Equipment", "brand_wikidata": "Q43379813"}
    start_urls = ["https://www.northerntool.com/wcs/resources/store/6970/storelocator/location?country=USA"]
    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "DEFAULT_REQUEST_HEADERS": {
            "User-Agent": FIREFOX_LATEST,
            "Accept": "application/json, text/plain, */*",
            "Referer": "https://www.northerntool.com/store-locator",
        },
    }

    def parse(self, response):
        stores = response.json()["PhysicalStore"]
        for store in stores:
            item = DictParser.parse(store)
            item["branch"] = item.pop("name")
            item["ref"] = store["uniqueID"]
            item["website"] = "https://www.northerntool.com/store/" + store["x_url"]
            yield item
