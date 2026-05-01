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
        for prefix, name in [("Jacobs ", "Jacobs"), ("CC Mat ", "CC Mat"), ("MENY ", "Meny")]:
            if raw_name.startswith(prefix):
                item["name"] = name
                item["branch"] = raw_name.removeprefix(prefix)
                break
        else:
            item["name"] = raw_name
        yield item
