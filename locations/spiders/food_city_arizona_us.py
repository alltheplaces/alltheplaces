from locations.spiders.raleys_us import RaleysUSSpider


class FoodCityArizonaUSSpider(RaleysUSSpider):
    name = "food_city_arizona_us"
    allowed_domains = ["www.mifoodcity.com"]
