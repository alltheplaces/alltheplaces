from locations.categories import Categories
from locations.storefinders.wp_go_maps import WPGoMapsSpider


class MirabitoUSSpider(WPGoMapsSpider):
    name = "mirabito_us"
    item_attributes = {"brand": "Rosauers Supermarkets", "extras": Categories.SHOP_CONVENIENCE.value}
    allowed_domains = ["www.mirabito.com"]
