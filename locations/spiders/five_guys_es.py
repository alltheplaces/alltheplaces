from locations.spiders.five_guys_us import FiveGuysUSSpider
from locations.storefinders.yext_answers import YextAnswersSpider


class FiveGuysESSpider(YextAnswersSpider):
    name = "five_guys_es"
    item_attributes = FiveGuysUSSpider.item_attributes
    api_key = "8305fbf269956ad9f4ebacaa7363a875"
    experience_key = "search-backend-es"
    locale = "es"
