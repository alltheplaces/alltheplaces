from locations.spiders.nandos_za import NandosZASpider


class NandosZMSpider(NandosZASpider):
    name = "nandos_zm"
    start_urls = [
        "https://api.locationbank.net/storelocator/StoreLocatorAPI?clientId=217d500d-5c3c-4220-9e52-cabb2ad6a7d3"
    ]
    web_root = "https://store.nandos.co.zm/details/"
