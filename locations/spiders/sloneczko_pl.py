from locations.categories import Categories
from locations.hours import DAYS_EN
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class SloneczkoPLSpider(WPStoreLocatorSpider):
    name = "sloneczko_pl"
    item_attributes = {
        "brand_wikidata": "Q113230439",
        "brand": "Słoneczko",
        "extras": Categories.SHOP_CONVENIENCE.value,
    }
    allowed_domains = [
        "sloneczko.zgora.pl",
    ]
    iseadgg_countries_list = ["PL"]
    search_radius = 24
    max_results = 50
    days = DAYS_EN
