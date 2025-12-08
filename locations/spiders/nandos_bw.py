from locations.spiders.nandos_za import NandosZASpider


class NandosBWSpider(NandosZASpider):
    name = "nandos_bw"
    start_urls = [
        "https://api.locationbank.net/storelocator/StoreLocatorAPI?clientId=845ea9ce-06fd-447e-a871-0c26ec16c0bb"
    ]
    web_root = "https://store.nandos.co.bw/details/"
