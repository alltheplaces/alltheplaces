from locations.storefinders.wakefern import WakefernSpider


class ShopriteSpider(WakefernSpider):
    name = "shoprite"
    item_attributes = {"brand": "ShopRite", "brand_wikidata": "Q7501097"}
    start_urls = ["https://www.shoprite.com/"]
