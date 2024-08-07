from locations.items import Feature
from locations.storefinders.agile_store_locator import AgileStoreLocatorSpider


class TopMarketPLSpider(AgileStoreLocatorSpider):
    name = "top_market_pl"
    item_attributes = {"brand": "Top Market", "brand_wikidata": "Q9360044"}
    start_urls = ["https://www.topmarkety.pl/wp-admin/admin-ajax.php?action=asl_load_stores&load_all=1&layout=1"]

    def parse_item(self, item: Feature, location: dict, **kwargs):
        del item["website"]
        yield item
