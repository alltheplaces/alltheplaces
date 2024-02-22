from html import unescape

from locations.categories import Categories
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class BashasUSSpider(WPStoreLocatorSpider):
    name = "bashas_us"
    item_attributes = {
        "brand": "Bashas'",
        "brand_wikidata": "Q4866786",
        "extras": Categories.SHOP_SUPERMARKET.value,
    }
    allowed_domains = ["www.bashas.com"]
    searchable_points_files = ["us_centroids_iseadgg_458km_radius.csv"]
    search_radius = 500
    max_results = 100
    time_format = "%I:%M %p"

    def parse_item(self, item, location):
        item["name"] = unescape(item["name"])
        yield item
