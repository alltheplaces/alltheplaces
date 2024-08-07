from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.agile_store_locator import AgileStoreLocatorSpider


class SuzukiCASpider(AgileStoreLocatorSpider):
    name = "suzuki_ca"
    item_attributes = {"brand": "Suzuki", "brand_wikidata": "Q181642"}
    start_urls = [
        "https://www.suzuki.ca/wp-admin/admin-ajax.php?action=asl_load_stores&nonce=811ab7901d&load_all=1&layout=1"
    ]

    def parse_item(self, item: Feature, location: dict, **kwargs):
        apply_category(Categories.SHOP_CAR, item)

        yield item
