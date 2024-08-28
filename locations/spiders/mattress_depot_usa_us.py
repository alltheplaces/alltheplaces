from locations.categories import Categories
from locations.hours import DAYS_EN
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class MattressDepotUsaUSSpider(WPStoreLocatorSpider):
    name = "mattress_depot_usa_us"
    item_attributes = {
        "brand": "Mattress Depot USA",
        "brand_wikidata": "Q108413386",
        "extras": Categories.SHOP_BED.value,
    }
    drop_attributes = {"addr_full"}
    allowed_domains = ["www.mattressdepotusa.com"]
    days = DAYS_EN
