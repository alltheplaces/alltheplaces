from typing import Any, Iterable

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.items import Feature
from locations.storefinders.yext import YextSpider


class OzkBankUSSpider(YextSpider):
    name = "ozk_bank_us"
    item_attributes = {"brand": "Bank OZK", "brand_wikidata": "Q20708654"}
    api_key = "7ae7edcf0b6af836f93b52ccd3bd2cf5"
    wanted_types = ["location", "atm"]

    def parse_item(self, item: Feature, location: dict, **kwargs: Any) -> Iterable[Feature]:
        entity_type = location.get("meta", {}).get("entityType")

        if entity_type == "atm":
            apply_category(Categories.ATM, item)
        elif entity_type == "location":
            services = location.get("c_servicesSection", {}).get("services", [])
            apply_category(Categories.BANK, item)
            apply_yes_no(Extras.ATM, item, "ATMs" in services)
            apply_yes_no(Extras.DRIVE_THROUGH, item, "Drive-Thru Banking" in services)
            apply_yes_no(Extras.CASH_IN, item, "ATM Deposits" in services)

            if drive_hours := location.get("driveThroughHours"):
                item["extras"]["opening_hours:drive_through"] = self.parse_opening_hours(drive_hours).as_opening_hours()

        yield item
