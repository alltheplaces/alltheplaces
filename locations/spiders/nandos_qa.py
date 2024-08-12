from locations.spiders.nandos_za import NandosZASpider


class NandosQASpider(NandosZASpider):
    name = "nandos_qa"
    client_id = "4204d252-cd2d-4dc3-a548-133bd26a9b2e"
    start_urls = ["https://api.locationbank.net/storelocator/StoreLocatorAPI?clientId=" + client_id]
    web_root = "https://store.nandos.qa/details/"
