from locations.categories import Categories
from locations.storefinders.wakefern import WakefernSpider


class GourmetGarageUSSpider(WakefernSpider):
    name = "gourmet_garage_us"
    item_attributes = {
        "brand": "Gourmet Garage",
        "brand_wikidata": "Q16994340",
        "name": "Gourmet Garage",
        "extras": Categories.SHOP_SUPERMARKET.value,
    }
    start_urls = ["https://www.gourmetgarage.com/"]
