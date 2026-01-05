from locations.hours import DAYS_EN
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class CookoutUSSpider(WPStoreLocatorSpider):
    name = "cookout_us"
    item_attributes = {"brand": "Cook Out", "brand_wikidata": "Q5166992"}
    allowed_domains = ["cookout.com"]
    searchable_points_files = ["us_centroids_50mile_radius_state.csv"]
    area_field_filter = ["AL", "GA", "KY", "MD", "MS", "NC", "SC", "TN", "VA", "WV"]
    search_radius = 50
    max_results = 50
    days = DAYS_EN

    def post_process_item(self, item, response, store):
        if store.get("coming_soon"):
            return
        item["branch"] = item.pop("name")
        yield item
