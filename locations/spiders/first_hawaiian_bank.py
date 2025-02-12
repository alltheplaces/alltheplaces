from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.storefinders.sweetiq import SweetIQSpider


class FirstHawaiianBankSpider(SweetIQSpider):
    name = "first_hawaiian_bank"
    item_attributes = {"brand": "Hawaiian First Bank", "brand_wikidata": "Q3072937"}
    start_urls = ["https://locations.fhb.com/"]

    def parse_item(self, item, location):
        item.pop("website")
        if "metaFilterServices" not in location["properties"]:
            location["properties"]["metaFilterServices"] = location["properties"]["categories"]
        # Branch without an ATM
        if (
            "Branch" in location["properties"]["metaFilterServices"]
            and "ATM" not in location["properties"]["metaFilterServices"]
        ):
            apply_category(Categories.BANK, item)
        # Branch with an ATM
        elif (
            "Branch" in location["properties"]["metaFilterServices"]
            and "ATM" in location["properties"]["metaFilterServices"]
        ):
            apply_category(Categories.BANK, item)
            apply_yes_no(Extras.ATM, item, True)
        # ATM only
        elif (
            "Branch" not in location["properties"]["metaFilterServices"]
            and "ATM" in location["properties"]["metaFilterServices"]
        ):
            apply_category(Categories.ATM, item)
            item.pop("phone")
        yield item
