from locations.categories import Categories
from locations.storefinders.amai_promap import AmaiPromapSpider


class AmericanMattressUSSpider(AmaiPromapSpider):
    name = "american_mattress_us"
    start_urls = ["https://www.americanmattress.com/pages/store-locator"]
    item_attributes = {
        "brand": "American Mattress",
        "brand_wikidata": "Q126896153",
        "extras": Categories.SHOP_BED.value,
    }
