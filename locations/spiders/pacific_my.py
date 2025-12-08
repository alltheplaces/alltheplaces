from locations.categories import Categories
from locations.spiders.the_store_my import TheStoreMYSpider


class PacificMYSpider(TheStoreMYSpider):
    name = "pacific_my"
    item_attributes = {"brand": "Pacific", "brand_wikidata": "Q125449800", "extras": Categories.SHOP_SUPERMARKET.value}
    allowed_domains = ["www.tstore.com.my"]
    start_urls = ["https://www.tstore.com.my/pacific.php"]
