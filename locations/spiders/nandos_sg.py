from locations.spiders.nandos import NANDOS_SHARED_ATTRIBUTES
from locations.spiders.nandos_my import NandosMYSpider


class NandosSGSpider(NandosMYSpider):
    name = "nandos_sg"
    item_attributes = NANDOS_SHARED_ATTRIBUTES | {"country": "SG"}
    start_urls = ["https://www.nandos.com.sg/restaurants/__data.json"]
