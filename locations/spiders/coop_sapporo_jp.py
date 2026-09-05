from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.canly import CanlySpider


class CoopSapporoJPSpider(CanlySpider):
    name = "coop_sapporo_jp"
    item_attributes = {
        "brand": "COOP SAPPORO",
        "brand_wikidata": "Q11574624",
    }
    api_endpoint = "https://api.site.can-ly.com/v2/directories/91/shops/search"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["name"] = feature.get("brand").get("name")
        item["branch"] = feature.get("nameKanji")
        item["extras"]["branch:ja-Hira"] = feature.get("nameKana")
        item["website"] = f"https://map.sapporo.coop/store/detail/{feature.get('storeCode')}/"

        if feature.get("openStatus") != "IS_ALREADY_OPEN":
            # Temporarily closed locations (for example, closed for renovation)
            item["extras"]["disused:shop"] = "supermarket"
        else:
            apply_category(Categories.SHOP_SUPERMARKET, item)

        yield item
