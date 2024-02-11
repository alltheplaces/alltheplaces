
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class CycleSpotJPSpider(WPStoreLocatorSpider):
        name = "cycle_spot_jp"
        item_attributes = {
                "brand_wikidata": "Q93620124",
                "brand": "サイクルスポット",
        }
        allowed_domains = [
                "www.cyclespot.net",
        ]