from locations.spiders.nandos_za import NandosZASpider


class NandosOMSpider(NandosZASpider):
    name = "nandos_om"
    start_urls = [
        "https://api.locationbank.net/storelocator/StoreLocatorAPI?clientId=90338503-bd4f-4b54-bb94-bb002f2717ec"
    ]
    web_root = "https://store.nandosoman.com/details/"
