from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.elfsight import ElfsightSpider


class AmigoPRSpider(ElfsightSpider):
    name = "amigo_pr"
    item_attributes = {"brand": "Amigo", "brand_wikidata": "Q4746234"}
    host = "core.service.elfsight.com"
    api_key = "5ffee2a7-32be-4ca7-8809-cec5d0a2e06f"

    def pre_process_data(self, feature: dict) -> None:
        if coordinates := feature.get("coordinates"):
            feature["coordinates"] = str(coordinates).replace(" ", ", ", 1)
        super().pre_process_data(feature)

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name").removeprefix("Amigo de ")
        apply_category(Categories.SHOP_SUPERMARKET, item)
        yield item
