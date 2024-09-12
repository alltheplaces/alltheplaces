from locations.storefinders.location_bank import LocationBankSpider


class AssupolZASpider(LocationBankSpider):
    name = "assupol_za"
    client_id = "f52b5825-1bd1-4ecb-8d0c-55dae6b7f0ea"
    item_attributes = {"brand": "Assupol", "brand_wikidata": "Q129269662"}
