from locations.categories import Categories
from locations.hours import DAYS_GR
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class MixMarktGRSpider(WPStoreLocatorSpider):
    days = DAYS_GR
    item_attributes = {"brand": "Mix Markt", "brand_wikidata": "Q327854", "extras": Categories.SHOP_SUPERMARKET.value}
    name = "mix_markt_gr"
    allowed_domains = [
        "www.mixmarkt.gr",
    ]
