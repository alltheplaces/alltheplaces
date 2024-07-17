from locations.categories import Categories
from locations.storefinders.woosmap import WoosmapSpider


class MonoprixFRSpider(WoosmapSpider):
    name = "monoprix_fr"
    item_attributes = {"brand": "Monoprix", "brand_wikidata": "Q3321241", "extras": Categories.SHOP_SUPERMARKET.value}
    key = "woos-ef21433b-45e1-3752-851f-6653279c035a"
    origin = "https://www.monoprix.fr"
