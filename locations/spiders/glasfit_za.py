from locations.storefinders.location_bank import LocationBankSpider


class GlasfitZASpider(LocationBankSpider):
    name = "glasfit_za"
    client_id = "183baa8e-6900-4556-bf9e-7b7eccfb0daf"
    item_attributes = {"brand": "Glasfit", "brand_wikidata": "Q126981121"}
