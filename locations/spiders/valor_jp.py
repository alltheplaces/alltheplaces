from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.canly import CanlySpider


class ValorJPSpider(CanlySpider):
    name = "valor_jp"
    item_attributes = {
        "brand": "バロー",
        "brand_wikidata": "Q11328346",
    }
    brand_key = "1245"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        # Skip any non-open locations
        if feature.get("businessStatus") != "OPEN":
            return

        item["branch"] = feature.get("nameKanji").removeprefix("スーパーマーケットバロー").strip()
        item["website"] = f"https://stores.valor.jp/detail/{feature.get('storeCode')}/"

        apply_category(Categories.SHOP_SUPERMARKET, item)

        yield item
