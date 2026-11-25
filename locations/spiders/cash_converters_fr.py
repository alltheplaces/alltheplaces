from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class CashConvertersFRSpider(JSONBlobSpider):
    name = "cash_converters_fr"
    item_attributes = {"brand": "Cash Converters", "brand_wikidata": "Q5048645"}
    start_urls = ["https://magasins.cashconverters.fr/api/store-locator/search?country=FR"]

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        name = item.pop("name", "")
        if "carrefour" not in name.lower():
            item["branch"] = name.removeprefix("Cash Converters ")
            item["website"] = f'https://magasins.cashconverters.fr/{feature.get("slug")})'
            apply_category(Categories.SHOP_PAWNBROKER, item)
            yield item
