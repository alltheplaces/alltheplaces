from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature


class TomMarketHUSpider(Spider):
    name = "tom_market_hu"
    item_attributes = {"brand": "Tom Market", "name": "Tom Market"}
    start_urls = ["https://tommarket.hu/hu/?mod=partners&cla=partners&fun=getPartnerCoordinates&ajax=1"]
    no_refs = True

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["partners"]:
            item = Feature()
            item["city"] = location["city"]
            item["branch"] = location["name"].removeprefix("Tom Market ")
            item["street_address"] = location["address"]
            item["lat"] = location["lat"]
            item["lon"] = location["lng"]
            item["postcode"] = location["zipcode"]

            apply_category(Categories.SHOP_CONVENIENCE, item)

            yield item
