from locations.storefinders.location_bank import LocationBankSpider


class BucoNAZASpider(LocationBankSpider):
    name = "buco_na_za"
    item_attributes = {"brand": "BUCO", "brand_wikidata": "Q116771533"}

    client_id = "fbd9d136-a3cf-4b2f-a0ac-29f20e30ab05"
