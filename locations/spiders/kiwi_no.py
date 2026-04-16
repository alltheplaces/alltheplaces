from typing import Iterable

from locations.items import Feature
from locations.storefinders.sylinder import SylinderSpider


class KiwiNOSpider(SylinderSpider):
    name = "kiwi_no"
    item_attributes = {"brand": "Kiwi", "brand_wikidata": "Q1613639"}
    app_keys = ["1100"]
    base_url = "https://kiwi.no/finn-butikk/"

    def parse_item(self, item: Feature, location: dict) -> Iterable[Feature]:
        branch = item.pop("name").removeprefix("KIWI ")
        branch_parts = branch.split(" ", 1)
        if len(branch_parts) == 2 and branch_parts[0].isdigit():
            branch = branch_parts[1]

        item["branch"] = branch
        yield item
