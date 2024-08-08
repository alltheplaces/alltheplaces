from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.agile_store_locator import AgileStoreLocatorSpider


class FiatDKSpider(AgileStoreLocatorSpider):
    name = "fiat_dk"
    item_attributes = {"brand": "Fiat", "brand_wikidata": "Q27597"}
    start_urls = [
        "https://interaction.fiat.dk/wp-admin/admin-ajax.php?action=asl_load_stores&nonce=f01f079120&lang=&load_all=1&layout=1"
    ]

    def parse_item(self, item: Feature, location: dict, **kwargs):
        if " | " in item["name"]:
            item["name"] = item["name"].split(" | ")[1]
        apply_category(Categories.SHOP_CAR, item)
        yield item
