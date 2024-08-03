from locations.storefinders.wp_go_maps import WpGoMapsSpider
from locations.categories import Categories


class EzMartUSSpider(WpGoMapsSpider):
    item_attributes = {"brand": "EZ Mart", "category": Categories.SHOP_CONVENIENCE}
    name = "ez_mart_us"
    allowed_domains = [
        "blarneycastleoil.com",
    ]
