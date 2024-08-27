from locations.categories import Categories
from locations.hours import DAYS_PL
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class NaszSklepPLSpider(WPStoreLocatorSpider):
    name = "nasz_sklep_pl"
    item_attributes = {
        "brand_wikidata": "Q62070369",
        "brand": "Nasz Sklep",
        "extras": Categories.SHOP_CONVENIENCE.value,
    }
    allowed_domains = [
        "nasz-sklep.pl",
    ]
    iseadgg_countries_list = ["PL"]
    search_radius = 24
    max_results = 100
    days = DAYS_PL
