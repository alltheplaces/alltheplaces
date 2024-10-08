from locations.spiders.five_guys_us import FIVE_GUYS_SHARED_ATTRIBUTES, FiveGuysUSSpider

# Five Guys YextSearch


class FiveGuysCASpider(FiveGuysUSSpider):
    name = "five_guys_ca"
    item_attributes = FIVE_GUYS_SHARED_ATTRIBUTES
    host = "https://restaurants.fiveguys.ca"
