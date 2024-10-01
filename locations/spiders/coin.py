from locations.categories import Categories, apply_category
from locations.json_blob_spider import JSONBlobSpider


class CoinSpider(JSONBlobSpider):
    name = "coin"
    STORE_TYPES = {
        "COIN": {"brand": "Coin", "brand_wikidata": "Q1107215"},
        "COINCASA": {"brand": "Coincasa", "brand_wikidata": "Q1107215"},
        "EXCELSIOR": {"brand": "Coin Excelsior", "brand_wikidata": "Q1107215"},
    }
    STORE_CATS = {
        "COIN": Categories.SHOP_DEPARTMENT_STORE,
        "COINCASA": Categories.SHOP_INTERIOR_DECORATION,
        "EXCELSIOR": Categories.SHOP_DEPARTMENT_STORE,
    }
    start_urls = [
        "https://www.coin.it/on/demandware.store/Sites-coin_eu-Site/it_IT/Stores-FindStores?latmin=-45&latmax=80&lngmin=-180&lngmax=180"
    ]
    locations_key = "stores"

    def post_process_item(self, item, response, location):
        item["website"] = location.get("detailPage")
        item["image"] = location["image"]
        store_type = location["storeType"]
        if brand_info := self.STORE_TYPES.get(store_type):
            item.update(brand_info)
            apply_category(self.STORE_CATS.get(store_type), item)
            yield item
        else:
            self.logger.error(f"unknown store type: {store_type}")
    drop_attributes = {"image"}
