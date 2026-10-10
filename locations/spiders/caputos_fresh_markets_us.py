from typing import Any, Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class CaputosFreshMarketsUSSpider(StructuredDataSpider):
    name = "caputos_fresh_markets_us"
    item_attributes = {
        "brand": "Angelo Caputo's Fresh Markets",
        "brand_wikidata": "Q118594294",
        "name": "Angelo Caputo's Fresh Markets",
    }
    allowed_domains = ["www.shopcaputos.com"]
    start_urls = ["https://www.shopcaputos.com/locations"]
    wanted_types = ["GroceryStore"]
    drop_attributes = {"image"}

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs: Any) -> Iterable[Feature]:
        item["branch"] = item.pop("name").removeprefix("Angelo Caputo's Fresh Markets").strip(" -")

        apply_category(Categories.SHOP_SUPERMARKET, item)

        yield item
