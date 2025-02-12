from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import merge_address_lines


class ChssGBSpider(Spider):
    name = "chss_gb"
    item_attributes = {
        "name": "Chest, Heart and Stroke Scotland",
        "brand": "Chest, Heart and Stroke Scotland",
        "brand_wikidata": "Q30265706",
    }
    start_urls = [
        "https://www.chss.org.uk/wp-admin/admin-ajax.php?action=store_search&lat=56.81&lng=-4.18&max_results=50&search_radius=200"
    ]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json():
            item = DictParser.parse(location)
            item["branch"] = location["store"]
            item["street_address"] = merge_address_lines([item.pop("addr_full"), location["address2"]])

            apply_category(Categories.SHOP_CHARITY, item)

            # TODO Opening hours

            yield item
