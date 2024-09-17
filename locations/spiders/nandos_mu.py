from locations.spiders.nandos_za import NandosZASpider


class NandosMUSpider(NandosZASpider):
    name = "nandos_mu"
    start_urls = [
        "https://api.locationbank.net/storelocator/StoreLocatorAPI?clientId=0185b030-fab6-4ab5-a111-3c7b86b33c13"
    ]
    web_root = "https://store.nandos.mu/details/"
