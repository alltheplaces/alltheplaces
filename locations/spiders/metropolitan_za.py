from locations.storefinders.location_bank import LocationBankSpider


class MetropolitanZASpider(LocationBankSpider):
    name = "metropolitan_za"
    client_id = "5b04a2d1-864a-43dd-9d0e-8ad018da9cdf"
    item_attributes = {"brand": "Metropolitan", "brand_wikidata": "Q129268975"}
