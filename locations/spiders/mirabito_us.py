from locations.categories import Categories
from locations.storefinders.wp_go_maps import WpGoMapsSpider


class MirabitoUSSpider(WpGoMapsSpider):
    name = "mirabito_us"
    item_attributes = {"brand": "Mirabito", "brand_wikidata": "Q126489051", "extras": Categories.SHOP_CONVENIENCE.value}
    allowed_domains = ["www.mirabito.com"]
    map_id = 1
    requires_proxy = "US"  # Geoblocking in use.
