from locations.spiders.nandos_za import NandosZASpider


class NandosZWSpider(NandosZASpider):
    name = "nandos_zw"
    client_id = "c8ca9649-9a2a-4338-8809-63dc2ac37da0"
    start_urls = ["https://api.locationbank.net/storelocator/StoreLocatorAPI?clientId=" + client_id]
    web_root = "https://store.nandos.co.zw/details/"
