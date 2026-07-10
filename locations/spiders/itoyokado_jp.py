from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.canly import CanlySpider


class ItoyokadoJPSpider(CanlySpider):
    name = "itoyokado_jp"
    item_attributes = {
        "brand": "イトーヨーカドー",
        "brand_wikidata": "Q3088746",
    }
    api_endpoint = "https://api.site.can-ly.com/v2/directories/55/shops/search"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        # Skip any non-open locations
        if feature.get("openStatus") != "IS_ALREADY_OPEN":
            return

        item["branch"] = feature.get("nameKanji").removeprefix("イトーヨーカドー ")
        item["extras"]["branch:ja-Hira"] = feature.get("nameKana").removeprefix("イトーヨーカドー ")
        item["website"] = f"https://stores.itoyokado.co.jp/detail/{feature.get('storeCode')}/"

        apply_category(Categories.SHOP_SUPERMARKET, item)

        yield item
