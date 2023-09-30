from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class CooplandsGBSpider(WPStoreLocatorSpider):
    name = "cooplands_gb"
    item_attributes = {"brand": "Cooplands", "brand_wikidata": "Q5167971"}
    allowed_domains = ["cooplands-bakery.co.uk"]
    searchable_points_files = ["gb_centroids_iseadgg_48km_radius.csv"]
    search_radius = 50
    max_results = 50
    time_format = "%I:%M %p"

    # def parse_item(self, item, location):
    # item["addr_full"] = location["address"]
    # item.pop("street_address", None)
    # yield item
