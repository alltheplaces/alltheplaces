from locations.hours import DAYS_GR
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class MixMarktGRSpider(WPStoreLocatorSpider):
    days = DAYS_GR
    name = "mix_markt_gr"
    allowed_domains = [
        "www.mixmarkt.gr",
    ]
