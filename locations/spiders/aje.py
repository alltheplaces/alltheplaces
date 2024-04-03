from locations.categories import Categories
from locations.storefinders.storemapper import StoremapperSpider


class AjeSpider(StoremapperSpider):
    name = "aje"
    item_attributes = {"brand": "Aje", "brand_wikidata": "Q118398985", "extras": Categories.SHOP_CLOTHES.value}
    key = "7370"

    def parse_item(self, item, location):
        if "AJE" not in item["name"].upper():
            return
        if "ATHLETICA" in item["name"].upper():
            item["brand"] = "Aje Athletica"
            item["brand_wikidata"] = "Q118398990"
        if "NEW ZEALAND" in item["addr_full"].upper():
            item["country"] = "NZ"
        yield item
