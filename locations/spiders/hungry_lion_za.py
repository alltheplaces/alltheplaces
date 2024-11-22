from locations.storefinders.location_bank import LocationBankSpider

HUNGRY_LION_SHARED_ATTRIBUTES = {"brand": "Hungry Lion", "brand_wikidata": "Q115636930"}


class HungryLionZASpider(LocationBankSpider):
    name = "hungry_lion_za"
    item_attributes = HUNGRY_LION_SHARED_ATTRIBUTES
    client_id = "77e472e1-fcc2-49e7-be2b-b630b28c0213"
