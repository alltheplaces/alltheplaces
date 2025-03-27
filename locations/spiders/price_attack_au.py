from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.stockinstore import StockInStoreSpider


class PriceAttackAUSpider(StockInStoreSpider):
    name = "price_attack_au"
    item_attributes = {"brand": "Price Attack", "brand_wikidata": "Q117747512"}
    api_site_id = "10069"
    api_widget_id = "76"
    api_widget_type = "product"
    api_origin = "https://www.priceattack.com.au"

    def parse_item(self, item: Feature, location: dict):
        item["branch"] = item.pop("name")
        item["website"] = "https://www.priceattack.com.au" + location["store_locator_page_url"]
        apply_category(Categories.SHOP_HAIRDRESSER_SUPPLY, item)
        yield item
