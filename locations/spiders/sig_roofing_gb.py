from locations.categories import Categories
from locations.hours import DAYS_EN
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class SigRoofingGBSpider(WPStoreLocatorSpider):
    name = "sig_roofing_gb"
    item_attributes = {"brand": "SIG Roofing", "brand_wikidata": "Q121435383", "extras": Categories.SHOP_TRADE.value}
    allowed_domains = ["www.sigroofing.co.uk"]
    iseadgg_countries_list = ["GB"]
    search_radius = 100
    max_results = 100
    days = DAYS_EN
