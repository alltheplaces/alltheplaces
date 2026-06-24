from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.spiders.sainsburys import SainsburysSpider
from locations.storefinders.closeby import ClosebySpider


class PatisserieValerieGBSpider(ClosebySpider):
    name = "patisserie_valerie_gb"
    item_attributes = {"brand": "Patisserie Valerie", "brand_wikidata": "Q22101966"}
    api_key = "f312dbbc1e1036a6e7b395fbd18aaf1f"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if branch_name := item.pop("name", None):
            if branch_name.startswith("Patisserie Valerie, "):
                item["branch"] = branch_name.removeprefix("Patisserie Valerie, ")
            elif branch_name.startswith("Sainsbury's, "):
                item["branch"] = branch_name.removeprefix("Sainsbury's, ")
                item["located_in"] = SainsburysSpider.SAINSBURYS["brand"]
                item["located_in_wikidata"] = SainsburysSpider.SAINSBURYS["brand_wikidata"]

        apply_category(Categories.CAFE, item)

        yield item
