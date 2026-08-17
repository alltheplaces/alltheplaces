from typing import Any

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import merge_address_lines
from locations.structured_data_spider import StructuredDataSpider


class PinchAPennyUSSpider(StructuredDataSpider):
    name = "pinch_a_penny_us"
    item_attributes = {"brand": "Pinch A Penny", "brand_wikidata": "Q121436109"}
    start_urls = ["https://pinchapenny.com/api/store/search?lat=28.5&lng=-81.4"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json()["data"]:
            item = DictParser.parse(store)
            item["name"] = None
            item["street_address"] = merge_address_lines([item.pop("addr_full"), store["address_extended"]])
            apply_category(Categories.SHOP_SWIMMING_POOL, item)
            yield item
