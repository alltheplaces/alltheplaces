from locations.hours import DAYS_EN
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class SunLoanUSSpider(WPStoreLocatorSpider):
    name = "sun_loan_us"
    item_attributes = {"brand": "Sun Loan", "brand_wikidata": "Q118725658"}
    allowed_domains = ["www.sunloan.com"]
    searchable_points_files = ["us_centroids_100mile_radius_state.csv"]
    search_radius = 100
    max_results = 50
    area_field_filter = ["TX", "NV", "AL", "MS", "OK", "IL", "TN", "NM"]
    days = DAYS_EN
