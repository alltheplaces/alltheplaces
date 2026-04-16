from typing import Iterable

from locations.categories import Categories
from locations.items import Feature
from locations.storefinders.sylinder import SylinderSpider


class StorcashNOSpider(SylinderSpider):
    name = "storcash_no"
    item_attributes = {"brand": "Storcash", "extras": Categories.SHOP_WHOLESALE.value}
    app_keys = [
        "5000",  # Bergen Storcash Storcash (NO)
        "5010",  # Storcash Partivare
        "5020",  # Sola Storcash
        "5030",  # Haugaland Storcash
        "5040",  # Kjørbekk Storcash
        "5050",  # Råbekken Storcash
        "5060",  # Tiller Storcash
        "5070",  # Sørlandet Storcash
        "5080",  # Buskerud Storcash
        "5090",  # Bodø Storcash
        "7412",  # Innlandet Storcash Tørr
    ]
    base_url = "https://storcash.no/butikker/"

    def parse_item(self, item: Feature, location: dict) -> Iterable[Feature]:
        branch = item.pop("name")
        branch = branch.removeprefix("Storcash Norge avd ").removeprefix("Storcash ")
        branch = branch.removesuffix(" Storcash")
        branch = " ".join(branch.replace(" Storcash ", " ").split())

        item["name"] = "Storcash"
        item["branch"] = branch
        yield item
