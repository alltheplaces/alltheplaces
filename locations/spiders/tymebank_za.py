import re

from locations.categories import Categories, apply_category
from locations.spiders.bash import BASH_BRANDS
from locations.storefinders.location_bank import LocationBankSpider

PICK_N_PAY_BRANDS = {
    "PNP": {
        "brand": "Pick n Pay",
        "brand_wikidata": "Q7190735",
    },
    "BOXER": {
        "brand": "Boxer",
        "brand_wikidata": "Q116586275",
    },
}


class TymebankZASpider(LocationBankSpider):
    name = "tymebank_za"
    client_id = "05c109b0-604d-4570-9ecf-fee8f55b18fd"
    item_attributes = {
        "brand": "TymeBank",
        "brand_wikidata": "Q65066197",
    }
    located_in_brands = BASH_BRANDS | PICK_N_PAY_BRANDS
    brand_name_regex = re.compile(r"^(" + "|".join(located_in_brands) + r") ", re.IGNORECASE)

    def post_process_item(self, item, response, location):
        apply_category(Categories.VENDING_MACHINE_GENERIC, item)
        item.pop("website")
        item["branch"] = item["branch"].removeprefix("Kiosk ")

        if m := self.brand_name_regex.match(item["branch"]):
            item["located_in"] = self.located_in_brands[m.group(1).upper()]["brand"]
            item["located_in_wikidata"] = self.located_in_brands[m.group(1).upper()]["brand_wikidata"]
        else:
            self.crawler.stats.inc_value(f"atp/{self.name}/located_in_failed/{item['branch']}")

        yield item
