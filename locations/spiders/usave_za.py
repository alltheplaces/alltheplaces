from locations.categories import Categories
from locations.spiders.medirite_za import MediriteZASpider


class UsaveZASpider(MediriteZASpider):
    name = "usave_za"
    item_attributes = {
        "brand": "Usave",
        "brand_wikidata": "Q115696368",
        "extras": Categories.SHOP_SUPERMARKET.value,
    }
    brands = ["Usave"]
    start_urls = ["https://www.usave.co.za/bin/stores.json?national=yes&brand=shoprite&country=198"]
    base_url = "https://www.usave.co.za"
