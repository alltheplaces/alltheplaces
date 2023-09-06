from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class BreadtopAUSpider(WPStoreLocatorSpider):
    name = "breadtop_au"
    item_attributes = {"brand": "Breadtop", "brand_wikidata": "Q4959217"}
    allowed_domains = ["www.breadtop.com.au"]
    searchable_points_files = ["au_centroids_iseadgg_175km_radius.csv"]
    search_radius = 200
    max_results = 50

    def parse_item(self, item, location):
        item["addr_full"] = location["address"]
        item.pop("street_address", None)
        yield item
