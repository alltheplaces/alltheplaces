from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class ProHockeyLifeCASpider(JSONBlobSpider):
    name = "pro_hockey_life_ca"
    item_attributes = {"brand": "Pro Hockey Life", "brand_wikidata": "Q123466336"}
    start_urls = ["https://www.prohockeylife.com/cdn/shop/t/37/assets/stores.json"]
    locations_key = "data"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name")

        apply_category(Categories.SHOP_SPORTS, item)

        yield item
