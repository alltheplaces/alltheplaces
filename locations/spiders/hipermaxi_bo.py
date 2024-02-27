from locations.categories import Categories, apply_category
from locations.storefinders.agile_store_locator import AgileStoreLocatorSpider


class HipermaxiBOSpider(AgileStoreLocatorSpider):
    name = "hipermaxi_bo"
    item_attributes = {
        "brand_wikidata": "Q81968262",
        "brand": "Hipermaxi",
    }
    allowed_domains = [
        "hipermaxi.com",
    ]

    def parse_item(self, item, location):
        if location["slug"].startswith("farmacia-"):
            apply_category(Categories.PHARMACY, item)
        if location["slug"].startswith("drugstore-"):
            apply_category(Categories.SHOP_CHEMIST, item)
        if location["slug"].startswith("hipermaxi-"):
            apply_category(Categories.SHOP_SUPERMARKET, item)
        yield item
