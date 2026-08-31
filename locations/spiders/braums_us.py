from locations.categories import apply_category
from locations.hours import DAYS_EN
from locations.items import Feature
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class BraumsUSSpider(WPStoreLocatorSpider):
    name = "braums_us"
    item_attributes = {"brand": "Braum's", "brand_wikidata": "Q4958263"}
    allowed_domains = ["www.braums.com"]
    # Braum's operates only in a handful of states, and the OKC metro area
    # is dense enough that a country-wide grid at this radius would risk
    # truncation there, so restrict the grid to the states it operates in.
    searchable_points_files = ["us_centroids_50mile_radius_state.csv"]
    area_field_filter = ["OK", "KS", "TX", "MO", "AR"]
    search_radius = 50
    max_results = 200
    days = DAYS_EN

    def post_process_item(self, item: Feature, response, feature: dict):
        item["branch"] = item.pop("name")
        apply_category(
            {"amenity": "fast_food", "shop": "dairy", "cuisine": "ice_cream;burger", "takeaway": "yes"}, item
        )
        yield item
