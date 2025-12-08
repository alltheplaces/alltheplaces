from locations.spiders.nandos_za import NandosZASpider


class NandosZWSpider(NandosZASpider):
    name = "nandos_zw"
    start_urls = [
        "https://api.locationbank.net/storelocator/StoreLocatorAPI?clientId=c8ca9649-9a2a-4338-8809-63dc2ac37da0"
    ]
    web_root = "https://store.nandos.co.zw/details/"
