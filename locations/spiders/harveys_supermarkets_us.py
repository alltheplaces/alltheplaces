from locations.categories import Categories
from locations.spiders.winn_dixie_us import WinnDixieUSSpider
from locations.user_agents import BROWSER_DEFAULT


class HarveysSupermarketsUSSpider(WinnDixieUSSpider):
    """
    This brand is owned by Southeastern Grocers (https://www.segrocers.com)
    who reuse the same store finder method for their other brand
    Winn-Dixie (spider: winn_dixie_us).
    """

    name = "harveys_supermarkets_us"
    item_attributes = {
        "brand": "Harveys Supermarkets",
        "brand_wikidata": "Q5677767",
        "extras": Categories.SHOP_SUPERMARKET.value,
    }
    allowed_domains = ["www.harveyssupermarkets.com"]
    start_urls = [
        "https://www.harveyssupermarkets.com/V2/storelocator/getStores?search=jacksonville,%20fl&strDefaultMiles=1000&filter="
    ]
    user_agent = BROWSER_DEFAULT
