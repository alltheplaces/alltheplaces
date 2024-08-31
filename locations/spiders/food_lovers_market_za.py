from locations.categories import Categories
from locations.json_blob_spider import JSONBlobSpider

FOOD_LOVERS_STORE_TYPES = {
    "Eatery": {"brand": "Food Lover's Eatery", "brand_wikidata": "Q130190599", "extras": Categories.FAST_FOOD.value},
    "Store": {
        "brand": "Food Lover's Market",
        "brand_wikidata": "Q65071570",
        "extras": Categories.SHOP_SUPERMARKET.value,
    },
}


class FoodLoversMarketZASpider(JSONBlobSpider):
    name = "food_lovers_market_za"
    start_urls = [
        "https://foodloversmarket.co.za/wp-admin/admin-ajax.php?action=process_store_data&flm_user_latitude=false&flm_user_longitude=false"
    ]

    def post_process_item(self, item, response, location):
        if location.get("store_type") in FOOD_LOVERS_STORE_TYPES:
            item.update(FOOD_LOVERS_STORE_TYPES[location.get("store_type")])
        else:
            self.logger.warning(f"Unknown store type: {location.get('store_type')}")
        item["branch"] = (
            item.pop("name").replace("&#8217;", "'").replace("&#8211;", "").replace(item.get("brand"), "").strip()
        )
        yield item
