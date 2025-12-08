from locations.categories import Categories
from locations.storefinders.wp_go_maps import WpGoMapsSpider


class EzMartUSSpider(WpGoMapsSpider):
    item_attributes = {"brand": "EZ Mart", "extras": Categories.SHOP_CONVENIENCE.value}
    name = "ez_mart_us"
    allowed_domains = [
        "blarneycastleoil.com",
    ]
