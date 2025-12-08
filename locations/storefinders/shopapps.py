from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.dict_parser import DictParser
from locations.items import Feature

# This is an undocumented application forming part of the ShopApps
# suite of Shopify apps mentioned at https://shopapps.in/
#
# To use this spider, specify the "key" parameter that is unique
# to the brand. If additional fields need to be parsed, or some
# data needing to be cleaned, override the parse_item function.


class ShopAppsSpider(Spider):
    dataset_attributes = {"source": "api", "api": "shopapps.site"}
    key: str = ""
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def start_requests(self):
        yield JsonRequest(
            url=f"https://stores.shopapps.site/front-end/get_surrounding_stores.php?shop={self.key}&latitude=0&longitude=0&max_distance=0&limit=10000"
        )

    def parse(self, response: Response):
        for location in response.json()["stores"]:
            item = DictParser.parse(location)
            item.pop("addr_full", None)
            item["street_address"] = ", ".join(filter(None, [location.get("address"), location.get("address2")]))
            item["postcode"] = location.get("postal_zip")
            item["state"] = location.get("prov_state")
            yield from self.parse_item(item, location) or []

    def parse_item(self, item: Feature, location: dict):
        yield item
