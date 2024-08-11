from scrapy.http import JsonRequest

from locations.geo import point_locations
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class SloneczkoPLSpider(WPStoreLocatorSpider):
    name = "sloneczko_pl"
    item_attributes = {
        "brand_wikidata": "Q113230439",
        "brand": "Słoneczko",
    }
    allowed_domains = [
        "sloneczko.zgora.pl",
    ]
    searchable_points_files = [
        "eu_centroids_20km_radius_country.csv",
    ]
    max_results = 50
    search_radius = 20

    # See also https://github.com/alltheplaces/alltheplaces/pull/9369/files
    def start_requests(self):
        if len(self.start_urls) == 0 and hasattr(self, "allowed_domains"):
            for domain in self.allowed_domains:
                if len(self.searchable_points_files) > 0 and self.search_radius != 0 and self.max_results != 0:
                    for searchable_points_file in self.searchable_points_files:
                        for lat, lon in point_locations(searchable_points_file, "PL"):
                            yield JsonRequest(
                                url=f"https://{domain}/wp-admin/admin-ajax.php?action=store_search&lat={lat}&lng={lon}&max_results={self.max_results}&search_radius={self.search_radius}"
                            )
                else:
                    yield JsonRequest(url=f"https://{domain}/wp-admin/admin-ajax.php?action=store_search&autoload=1")
