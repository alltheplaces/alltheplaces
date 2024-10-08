from locations.spiders.nandos_za import NandosZASpider


class NandosINSpider(NandosZASpider):
    name = "nandos_in"
    start_urls = [
        "https://api.locationbank.net/storelocator/StoreLocatorAPI?clientId=85c0345d-9a0d-4ba4-b7d2-d6ba41f5d32c"
    ]
    web_root = "https://store.nandosindia.com/details/"
