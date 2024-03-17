from locations.hours import DAYS_EN
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class GoGamesToysUSSpider(WPStoreLocatorSpider):
    name = "go_games_toys_us"
    item_attributes = {
        "brand_wikidata": "Q108312837",
        "brand": "Go! Games & Toys",
    }
    allowed_domains = [
        "goretailgroup.com",
    ]
    max_results = 100
    search_radius = 500
    # https://goretailgroup.com/wp-admin/admin-ajax.php?action=store_search&lat=29.42519&lng=-98.49459&max_results=100&search_radius=500
    # Max is 500 miles
    searchable_points_files = [
        "us_centroids_iseadgg_458km_radius.csv",
    ]
    days = DAYS_EN

    def parse_item(self, item, location):
        if item["name"] == "Attic Salt":
            item["brand"] = "Attic Salt"
            item["brand_wikidata"] = "Q108409773"

        yield item
