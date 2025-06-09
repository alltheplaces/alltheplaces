from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories
from locations.dict_parser import DictParser
from locations.hours import DAYS_EN


class SelfastZASpider(Spider):
    name = "selfast_za"
    item_attributes = {"brand_wikidata": "Q116861449", "brand": "Selfast", "extras": Categories.SHOP_CLOTHES.value}
    allowed_domains = ["shop.selfast.co.za"]
    days = DAYS_EN
    start_urls = [
        "https://selfast.co.za/wp-admin/admin-ajax.php?action=store_search&lat=-25.7565723&lng=28.1913815&search_radius=500&autoload=1"
    ]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json():
            item = DictParser.parse(location)
            item["branch"] = location["store"]
            yield item
