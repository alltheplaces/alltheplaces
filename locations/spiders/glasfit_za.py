from locations.storefinders.location_bank import LocationBankSpider


class GlasfitZASpider(LocationBankSpider):
    name = "glasfit_za"
    client_id = "800c7571-4e99-4efc-97e7-14983b507e31"
    item_attributes = {"brand": "Glasfit", "brand_wikidata": "Q126981121"}
