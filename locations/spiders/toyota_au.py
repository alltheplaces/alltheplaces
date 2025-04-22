from json import loads
from typing import Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.dict_parser import DictParser
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS_WITH_EXT_JS
from locations.user_agents import BROWSER_DEFAULT

TOYOTA_SHARED_ATTRIBUTES = {"brand": "Toyota", "brand_wikidata": "Q53268"}


class ToyotaAUSpider(Spider):
    name = "toyota_au"
    item_attributes = TOYOTA_SHARED_ATTRIBUTES
    allowed_domains = ["www.toyota.com.au"]
    start_urls = [
        "https://www.toyota.com.au/main/api/v1/toyotaforms/info/dealersbystate/ACT?dealerOptIn=false",
        "https://www.toyota.com.au/main/api/v1/toyotaforms/info/dealersbystate/NSW?dealerOptIn=false",
        "https://www.toyota.com.au/main/api/v1/toyotaforms/info/dealersbystate/NT?dealerOptIn=false",
        "https://www.toyota.com.au/main/api/v1/toyotaforms/info/dealersbystate/QLD?dealerOptIn=false",
        "https://www.toyota.com.au/main/api/v1/toyotaforms/info/dealersbystate/SA?dealerOptIn=false",
        "https://www.toyota.com.au/main/api/v1/toyotaforms/info/dealersbystate/TAS?dealerOptIn=false",
        "https://www.toyota.com.au/main/api/v1/toyotaforms/info/dealersbystate/VIC?dealerOptIn=false",
        "https://www.toyota.com.au/main/api/v1/toyotaforms/info/dealersbystate/WA?dealerOptIn=false",
    ]
    user_agent = BROWSER_DEFAULT
    is_playwright_spider = True
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS_WITH_EXT_JS

    def parse(self, response: Response) -> Iterable[Feature]:
        json_blob = loads(response.xpath("//pre/text()").get())
        for location in json_blob["results"]:
            for location_type in ["sales", "service", "parts"]:
                if not location[location_type]:
                    continue

                item = DictParser.parse(location)
                item["ref"] = location["branchCode"] + "_" + location_type
                item["lat"] = location["refY"]
                item["lon"] = location["refX"]
                item["state"] = location["state"]
                item["street_address"] = item.pop("addr_full", None)
                item["website"] = location["webSite"]

                if location_type == "sales":
                    apply_category(Categories.SHOP_CAR, item)
                elif location_type == "service":
                    apply_category(Categories.SHOP_CAR_REPAIR, item)
                elif location_type == "parts":
                    apply_category(Categories.SHOP_CAR_PARTS, item)

                yield item
