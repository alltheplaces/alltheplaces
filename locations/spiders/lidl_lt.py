from locations.hours import DAYS_ES
from locations.spiders.lidl_at import LidlATSpider


class LidlLTSpider(LidlATSpider):
    name = "lidl_lt"

    dataset_id = "8a2167d4bd8a47d9930fc73f5837f0bf"
    dataset_name = "Filialdaten-LT/Filialdaten-LT"
    api_key = "AkEdcFBe-gxNmSmCIpOKE_KuLBZv-NHRKY_ndbJKiVvc0ramz4hZKta-rZRpuNZS"
    days = DAYS_ES
