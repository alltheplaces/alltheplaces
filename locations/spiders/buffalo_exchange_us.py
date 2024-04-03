from urllib.parse import urljoin

from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class BuffaloExchangeUSSpider(WPStoreLocatorSpider):
    name = "buffalo_exchange_us"
    item_attributes = {
        "brand_wikidata": "Q4985721",
        "brand": "Buffalo Exchange",
    }
    allowed_domains = [
        "buffaloexchange.com",
    ]
    time_format = "%I:%M %p"
    searchable_points_files = ["us_centroids_iseadgg_458km_radius.csv"]
    search_radius = 1000
    max_results = 100

    def parse_item(self, item, location):
        item["website"] = urljoin("https://buffaloexchange.com", item["website"])

        yield item
