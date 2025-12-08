from locations.categories import Categories
from locations.spiders.the_store_my import TheStoreMYSpider


class MilimewaMYSpider(TheStoreMYSpider):
    name = "milimewa_my"
    item_attributes = {"brand": "Milimewa", "brand_wikidata": "Q125449813", "extras": Categories.SHOP_SUPERMARKET.value}
    allowed_domains = ["www.tstore.com.my"]
    start_urls = ["https://www.tstore.com.my/milimewa.php"]
