from locations.categories import Categories
from locations.storefinders.wakefern import WakefernSpider


class TheFreshGrocerUSSpider(WakefernSpider):
    name = "the_fresh_grocer_us"
    item_attributes = {
        "brand": "The Fresh Grocer",
        "brand_wikidata": "Q18389721",
        "name": "The Fresh Grocer",
        "extras": Categories.SHOP_SUPERMARKET.value,
    }
    start_urls = ["https://www.thefreshgrocer.com/"]
    requires_proxy = True
