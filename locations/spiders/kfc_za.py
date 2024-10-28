from locations.spiders.kfc_au import KfcAUSpider


class KfcZASpider(KfcAUSpider):
    name = "kfc_za"

    region_code = "eu"
    tenant_id = "5f89a603781e4df48d31337a6c1252a8"
    web_root = "https://order.kfc.co.za/restaurants/"
