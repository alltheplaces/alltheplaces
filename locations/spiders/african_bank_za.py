from locations.categories import Categories, Extras, apply_yes_no
from locations.storefinders.location_bank import LocationBankSpider


class AfricanBankZASpider(LocationBankSpider):
    name = "african_bank_za"
    client_id = "6ef8638f-af8c-409d-ad24-cf3422269370"
    item_attributes = {"brand": "African Bank", "brand_wikidata": "Q4689703", "extras": Categories.BANK.value}

    def parse_item(self, item, location):
        apply_yes_no(Extras.ATM, item, "ATM" in location["slAttributes"])
        # Unhandled: "Business Services", "Specialized Services"
        yield item
