from locations.spiders.hungry_lion_za import HUNGRY_LION_SHARED_ATTRIBUTES
from locations.storefinders.location_bank import LocationBankSpider


class HungryLionAOSpider(LocationBankSpider):
    name = "hungry_lion_ao"
    item_attributes = HUNGRY_LION_SHARED_ATTRIBUTES
    client_id = "c4a1835e-1e57-449e-978e-544e05ab074e"
