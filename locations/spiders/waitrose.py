from typing import Iterable

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.items import Feature
from locations.storefinders.yext_answers import YextAnswersSpider


class WaitroseSpider(YextAnswersSpider):
    name = "waitrose"
    LITTLE_WAITROSE = {"brand": "Little Waitrose", "brand_wikidata": "Q771734"}
    WAITROSE = {"brand": "Waitrose", "brand_wikidata": "Q771734"}
    item_attributes = WAITROSE
    endpoint = "https://prod-cdn.us.yextapis.com/v2/accounts/me/search/vertical/query"
    experience_key = "waitrose-locator-search"
    api_key = "b89aa54de5943d5158a4d0b4062fe8d1"
    locale = "en-GB"

    def parse_item(self, location: dict, item: Feature) -> Iterable[Feature]:
        services = location.get("services", [])
        apply_yes_no(Extras.BABY_CHANGING_TABLE, item, "Baby Change Facility" in services)
        apply_yes_no(Extras.ATM, item, "Cash Point" in services)
        apply_yes_no(Extras.TOILETS, item, "Customer Toilets" in services)
        apply_yes_no("sells:lottery", item, "Lottery Counter" in services)
        apply_yes_no(Extras.WHEELCHAIR, item, "Wheelchair Trolleys Available" in services)

        if item["name"].startswith("Little Waitrose"):
            item.update(self.LITTLE_WAITROSE)
            item["name"] = "Little Waitrose"
            apply_category(Categories.SHOP_CONVENIENCE, item)
        else:
            item.update(self.WAITROSE)
            item["name"] = "Waitrose"
            apply_category(Categories.SHOP_SUPERMARKET, item)

        yield item
