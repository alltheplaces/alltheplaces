from locations.categories import Categories, apply_category
from locations.storefinders.rio_seo import RioSeoSpider


class GuessSpider(RioSeoSpider):
    name = "guess"
    item_attributes = {"brand": "Guess", "brand_wikidata": "Q2470307", "extras": Categories.SHOP_CLOTHES.value}
    end_point = "https://maps.stores.guess.com"

    def post_process_feature(self, feature, location):
        if location["store_type_cs"] == "Guess Accessories":
            apply_category(Categories.SHOP_FASHION_ACCESSORIES, feature)
        elif location["store_type_cs"] == "G by Guess":
            feature["brand_wikidata"] = "Q5515159"
        if location["store_type_cs"] not in ("Clothing Store,GUESS", ""):
            feature["brand"] = location["store_type_cs"]
        yield feature
