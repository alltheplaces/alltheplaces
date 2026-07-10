from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.canly import CanlySpider


class HeiwadoJPSpider(CanlySpider):
    name = "heiwado_jp"
    item_attributes = {
        "brand": "平和堂",
        "brand_wikidata": "Q11060757",
    }
    api_endpoint = "https://api.site.can-ly.com/v2/directories/6/shops/search"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        # Skip any non-open locations
        if feature.get("openStatus") != "IS_ALREADY_OPEN":
            return

        item["name"] = feature.get("brand").get("name")
        item["branch"] = feature.get("nameKanji")
        item["extras"]["branch:ja-Hira"] = feature.get("nameKana")
        item["website"] = f"https://shoplist.heiwado.jp/detail/{feature.get('storeCode')}/"

        apply_category(Categories.SHOP_SUPERMARKET, item)

        yield item
