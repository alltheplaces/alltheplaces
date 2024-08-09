
from locations.spiders.kfc_au import KfcAUSpider


class KfcZASpider(KfcAUSpider):
    name = "kfc_za"

    region_code = "eu"
    start_urls = ["https://orderserv-kfc-" + region_code + "-olo-api.yum.com/dev/v1/stores/"]
    tenant_id = "5f89a603781e4df48d31337a6c1252a8"
    web_root = "https://order.kfc.com.za/restaurants/"
    # requires_proxy = True  # May require ZA proxy, possibly residential IPs only.
