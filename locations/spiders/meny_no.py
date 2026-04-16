from typing import Iterable

from locations.items import Feature
from locations.storefinders.sylinder import SylinderSpider


class MenyNOSpider(SylinderSpider):
    name = "meny_no"
    item_attributes = {"brand": "Meny", "brand_wikidata": "Q10581720"}
    app_keys = ["1300"]
    base_url = "https://meny.no/finn-butikk/"

    def parse_item(self, item: Feature, location: dict) -> Iterable[Feature]:
        raw_name = item.pop("name")
        if raw_name.startswith("Jacobs "):
            item["name"] = "Jacobs"
            item["branch"] = raw_name.removeprefix("Jacobs ")
        elif raw_name.startswith("CC Mat "):
            item["name"] = "CC Mat"
            item["branch"] = raw_name.removeprefix("CC Mat ")
        elif raw_name.startswith("MENY "):
            item["name"] = "Meny"
            item["branch"] = raw_name.removeprefix("MENY ")
        else:
            item["name"] = raw_name

        yield item
