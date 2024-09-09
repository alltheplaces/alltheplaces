from locations.storefinders.location_bank import LocationBankSpider


class TalismanHireSpider(LocationBankSpider):
    name = "talisman_hire"
    client_id = "e291ff7a-451d-4eee-a25b-a834c9fe6eeb"
    item_attributes = {"brand": "Talisman Hire", "brand_wikidata": "Q120885726"}
