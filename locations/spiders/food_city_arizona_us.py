from locations.categories import Categories
from locations.spiders.raleys_us import RaleysUSSpider


class FoodCityArizonaUSSpider(RaleysUSSpider):
    name = "food_city_arizona_us"
    item_attributes = {
        "brand": "Food City",
        "brand_wikidata": "Q130253202",
        "extras": Categories.SHOP_SUPERMARKET.value,
    }
    allowed_domains = ["www.mifoodcity.com"]
