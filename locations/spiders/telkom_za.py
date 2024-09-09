from locations.storefinders.location_bank import LocationBankSpider


class TelkomZASpider(LocationBankSpider):
    name = "telkom_za"
    client_id = "800c7571-4e99-4efc-97e7-14983b507e31"
    item_attributes = {"brand": "Telkom", "brand_wikidata": "Q1818970"}
