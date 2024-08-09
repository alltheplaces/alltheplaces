from locations.spiders.kfc_au import KfcAUSpider


class KfcCASpider(KfcAUSpider):
    name = "kfc_ca"

    region_code = "na"
    tenant_id = "a087813cef074625a8341e162356a1e5"
    web_root = None
    requires_proxy = False
