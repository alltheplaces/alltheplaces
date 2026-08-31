from locations.spiders.nandos import NANDOS_SHARED_ATTRIBUTES
from locations.storefinders.location_bank import LocationBankSpider


class NandosQASpider(LocationBankSpider):
    name = "nandos_qa"
    item_attributes = NANDOS_SHARED_ATTRIBUTES
    client_id = "4204d252-cd2d-4dc3-a548-133bd26a9b2e"
