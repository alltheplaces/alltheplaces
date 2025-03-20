from locations.spiders.hungry_lion_za import HUNGRY_LION_SHARED_ATTRIBUTES
from locations.storefinders.location_bank import LocationBankSpider


class HungryLionZMSpider(LocationBankSpider):
    name = "hungry_lion_zm"
    item_attributes = HUNGRY_LION_SHARED_ATTRIBUTES
    client_id = "0ff90a58-0517-402a-a729-70394bf91128"
