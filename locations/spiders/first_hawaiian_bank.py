from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.storefinders.uberall import UberallSpider


class FirstHawaiianBankSpider(UberallSpider):
    name = "first_hawaiian_bank"
    item_attributes = {"brand": "Hawaiian First Bank", "brand_wikidata": "Q3072937"}
    key = "YBDTqfImunUKrrrbIivdwT2rDp8h2q"

    def post_process_item(self, item, response, location):
        name = location.get("name", "")

        # Branch without an ATM
        if "Branch" in name and "ATM" not in name:
            apply_category(Categories.BANK, item)
        # Branch with an ATM
        elif "Branch" in name and "ATM" in name:
            apply_category(Categories.BANK, item)
            apply_yes_no(Extras.ATM, item, True)
        # ATM only
        elif "ATM" in name:
            apply_category(Categories.ATM, item)
            item.pop("phone", None)
        yield item
