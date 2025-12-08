from locations.categories import Categories
from locations.storefinders.stockinstore import StockInStoreSpider


class CompleatAnglerCampingWorldAUSpider(StockInStoreSpider):
    name = "compleat_angler_camping_world_au"
    # Some stores are dual branded but there isn't really a
    # "located in" relationship.
    brands = {
        "COMPLEATANGLER": {
            "brand": "Compleat Angler",
            "brand_wikidata": "Q124062620",
            "extras": Categories.SHOP_FISHING.value,
        },
        "CAMPINGWORLD": {
            "brand": "Camping World",
            "brand_wikidata": "Q124062618",
            "extras": Categories.SHOP_OUTDOOR.value,
        },
        "COMPLEATANGLERCAMPINGWORLD": {
            "brand": "Compleat Angler & Camping World",
            "brand_wikidata": "Q124062620",
            "extras": Categories.SHOP_OUTDOOR.value,
        },
    }
    api_site_id = "10126"
    api_widget_id = "133"
    api_widget_type = "storelocator"
    api_origin = "https://compleatangler.com.au"

    def parse_item(self, item, location):
        item["website"] = "https://compleatangler.com.au" + location["store_locator_page_url"]
        if "COMPLEAT ANGLER" in item["name"].upper() and (
            "CAMPING WORLD" in item["name"].upper() or "CAMPING OUTDOORS" in item["name"].upper()
        ):
            item.update(self.brands["COMPLEATANGLERCAMPINGWORLD"])
        elif "COMPLEAT ANGLER" in item["name"].upper():
            item.update(self.brands["COMPLEATANGLER"])
        elif "CAMPING WORLD" in item["name"].upper() or "CAMPING OUTDOORS" in item["name"].upper():
            item.update(self.brands["CAMPINGWORLD"])
        yield item
