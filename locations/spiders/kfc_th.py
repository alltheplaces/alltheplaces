from locations.spiders.kfc_au import KfcAUSpider


class KfcTHSpider(KfcAUSpider):
    name = "kfc_za"

    region_code = "apac"
    tenant_id = "59dhhptudcn7hk1ogssvsb4cujvbcnh6o"
    web_root = "https://www.kfc.co.th/restaurants/"
