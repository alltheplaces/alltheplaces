from typing import Iterable

from locations.items import Feature
from locations.storefinders.sylinder import SylinderSpider


class NarbutikkenNOSpider(SylinderSpider):
    name = "narbutikken_no"
    item_attributes = {"brand": "Nærbutikken", "brand_wikidata": "Q108810007"}
    app_keys = ["1270"]
    base_url = "https://narbutikken.no/finn-butikk/"

    def parse_item(self, item: Feature, location: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name").removeprefix("Nærbutikken ")
        item["name"] = "Nærbutikken"
        yield item
