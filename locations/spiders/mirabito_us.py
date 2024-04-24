from locations.categories import Categories
from locations.storefinders.wp_go_maps import WpGoMapsSpider


class MirabitoUSSpider(WpGoMapsSpider):
    name = "mirabito_us"
    item_attributes = {"brand": "Rosauers Supermarkets", "extras": Categories.SHOP_CONVENIENCE.value}
    allowed_domains = ["www.mirabito.com"]
    map_id = 1
