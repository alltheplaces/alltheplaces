from typing import Iterable

from locations.items import Feature
from locations.storefinders.sylinder import SylinderSpider


class JokerNOSpider(SylinderSpider):
    name = "joker_no"
    item_attributes = {"brand": "Joker", "brand_wikidata": "Q716328"}
    app_keys = ["1220"]
    base_url = "https://joker.no/finn-butikk/"

    def parse_item(self, item: Feature, location: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name").removeprefix("Joker ").removeprefix("JOKER ")
        yield item
