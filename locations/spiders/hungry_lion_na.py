from locations.spiders.hungry_lion_za import HUNGRY_LION_SHARED_ATTRIBUTES
from locations.storefinders.location_bank import LocationBankSpider


class HungryLionNASpider(LocationBankSpider):
    name = "hungry_lion_na"
    item_attributes = HUNGRY_LION_SHARED_ATTRIBUTES
    client_id = "87651bf1-aceb-41da-993c-c6fa158636f3"
