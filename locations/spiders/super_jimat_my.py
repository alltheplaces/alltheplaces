from locations.categories import Categories
from locations.spiders.the_store_my import TheStoreMYSpider


class SuperJimatMYSpider(TheStoreMYSpider):
    name = "super_jimat_my"
    item_attributes = {
        "brand": "Super Jimat",
        "brand_wikidata": "Q125449830",
        "extras": Categories.SHOP_SUPERMARKET.value,
    }
    allowed_domains = ["www.tstore.com.my"]
    start_urls = ["https://www.tstore.com.my/superjimat.php"]
