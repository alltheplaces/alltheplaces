from locations.categories import Categories, apply_category
from locations.hours import DAYS
from locations.storefinders.uberall import UberallSpider


class AldiNordFRSpider(UberallSpider):
    name = "aldi_nord_fr"
    item_attributes = {"name": "Aldi", "brand": "Aldi", "brand_wikidata": "Q41171373"}
    key = "ALDINORDFR_Mmljd17th8w26DMwOy4pScWk4lCvj5"

    def post_process_item(self, item, response, location):
        item["branch"] = item.pop("name").removeprefix("ALDI").strip() or None
        item["phone"] = None  # national customer service number, identical for every store

        # The Uberall storefinder skips days flagged as closed, losing the explicit closure.
        for rule in location["openingHours"]:
            if rule.get("closed"):
                item["opening_hours"].set_closed(DAYS[rule["dayOfWeek"] - 1])

        apply_category(Categories.SHOP_SUPERMARKET, item)

        yield item
