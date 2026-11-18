from typing import Iterable

from locations.items import Feature
from locations.storefinders.stockist import StockistSpider


class CrewClothingGBSpider(StockistSpider):
    name = "crew_clothing_gb"
    item_attributes = {"brand": "Crew Clothing Company", "brand_wikidata": "Q5184783"}
    key = "map_4q6e4y53"

    def parse_item(self, item: Feature, location: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        yield item
