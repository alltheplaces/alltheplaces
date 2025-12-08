from locations.spiders.nandos_za import NandosZASpider


class NandosBHSpider(NandosZASpider):
    name = "nandos_bh"
    start_urls = [
        "https://api.locationbank.net/storelocator/StoreLocatorAPI?clientId=3ab346a9-c73c-4c86-8c6e-9a8db5c1ef4e"
    ]
    web_root = "https://store.nandos.com.bh/details/"
