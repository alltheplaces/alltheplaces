from typing import Iterable

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.storerocket import StoreRocketSpider


class AthenaSpider(StoreRocketSpider):
    name = "athena"
    item_attributes = {"brand": "Athena Bitcoin", "brand_wikidata": "Q135280046"}
    storerocket_id = "vZ4v6A94Qd"
    time_hours_format = 12
    iseadgg_countries_list = ["US", "SV", "CO", "AR"]
    search_radius = 200

    def parse_item(self, item: Feature, location: dict) -> Iterable[Feature]:
        item["ref"] = str(item["ref"])
        item.pop("name", None)
        item.pop("facebook", None)
        item["extras"].pop("contact:instragram", None)

        for field in location.get("fields", {}):
            if field["name"] == "Located Inside:":
                item["located_in"] = field["pivot_field_value"]

        apply_category(Categories.ATM, item)
        item["extras"]["currency:XBT"] = "yes"
        item["extras"]["cash_in"] = "yes"
        match location.get("country"):
            case "Argentina":
                item["extras"]["currency:ARS"] = "yes"
            case "Colombia":
                item["extras"]["currency:COP"] = "yes"
            case "El Salvador":
                item["extras"]["currency:USD"] = "yes"
            case None | "":
                if location.get("timezone", "").startswith("America/") or location.get("phone").startswith("+1 "):
                    item["country"] = "US"
                    item["extras"]["currency:USD"] = "yes"
            case _:
                self.logger.warning(
                    "ATM is located in country '{}' for which the local currency is undefined by this spider. The spider should be updated to map a currency for this country.".format(
                        item.get("country")
                    )
                )

        yield item
