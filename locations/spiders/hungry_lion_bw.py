from locations.spiders.hungry_lion_za import HUNGRY_LION_SHARED_ATTRIBUTES
from locations.storefinders.location_bank import LocationBankSpider


class HungryLionBWSpider(LocationBankSpider):
    name = "hungry_lion_bw"
    item_attributes = HUNGRY_LION_SHARED_ATTRIBUTES
    client_id = "0352782e-7d03-433a-b411-2f6402aafa16"
