from typing import Any

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.items import Feature
from locations.storefinders.yext import YextSpider


class ChaseUSSpider(YextSpider):
    name = "chase_us"
    item_attributes = {"brand": "Chase", "brand_wikidata": "Q524629"}
    drop_attributes = {"twitter"}
    api_key = "e8996b1ad0e9b3a59e3d1251bbcc0b4b"
    api_version = "20240816"

    def parse_item(self, item: Feature, location: dict, **kwargs: Any) -> Any:
        item[
            "website"
        ] = f'https://www.chase.com/locator/banking/us/{item["state"]}/{item["city"]}/{item["street_address"]}'.lower().replace(
            " ", "-"
        )
        if item["name"] == "Chase Bank":
            item.pop("name")
            apply_category(Categories.BANK, item)
            apply_yes_no(Extras.ATM, item, location.get("c_primaryATM"))
        elif item["name"] == "Chase ATM":
            apply_category(Categories.ATM, item)

        yield item
