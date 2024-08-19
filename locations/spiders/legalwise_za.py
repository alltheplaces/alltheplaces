from locations.storefinders.location_bank import LocationBankSpider


class LegalwiseZASpider(LocationBankSpider):
    name = "legalwise_za"
    client_id = "1f58b485-a7fe-4fc2-b78a-41dd07f9f736"
    item_attributes = {"brand": "LegalWise", "brand_wikidata": "Q61442307"}
