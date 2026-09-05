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

        if start_date := feature.get("establishmentDate"):
            item["extras"]["start_date"] = start_date

        apply_category(Categories.SHOP_SUPERMARKET, item)

        if feature.get("openStatus") != "IS_ALREADY_OPEN":
            # API reports these as permanently closed, but they can be closed for
            # renovation and later reopen in the same place (e.g. 砂川 -> すながわ)
            item["extras"]["opening_hours"] = "closed"

        yield item
