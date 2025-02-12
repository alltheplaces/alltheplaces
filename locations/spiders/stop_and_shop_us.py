from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import merge_address_lines


class StopAndShopUSSpider(Spider):
    name = "stop_and_shop_us"
    item_attributes = {"brand": "Stop & Shop", "brand_wikidata": "Q3658429"}
    start_urls = [
        "https://stopandshop.com/apis/store-locator/locator/v1/stores/STSH?storeType=GROCERY&q=11797&maxDistance=1000000&details=true"
    ]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["stores"]:
            if not location["active"]:
                continue
            item = DictParser.parse(location)
            item["street_address"] = merge_address_lines([location["address1"], location["address2"]])

            apply_category(Categories.SHOP_SUPERMARKET, item)

            yield item
