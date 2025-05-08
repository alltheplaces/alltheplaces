from typing import Iterable

from scrapy.http import Response

from locations.items import Feature
from locations.storefinders.storeify import StoreifySpider


class TheBodyShopGBSpider(StoreifySpider):
    name = "the_body_shop_gb"
    item_attributes = {"brand": "The Body Shop", "brand_wikidata": "Q837851"}
    api_key = "the-body-shop-uk.myshopify.com"
    domain = "https://www.thebodyshop.com/"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name").removeprefix("The Body Shop ")
        yield item
