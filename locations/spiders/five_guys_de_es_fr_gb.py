from locations.spiders.five_guys_us import FiveGuysUSSpider
from locations.storefinders.yext import YextSpider


class FiveGuysDEESFRGBSpider(YextSpider):
    name = "five_guys_de_es_fr_gb"
    item_attributes = FiveGuysUSSpider.item_attributes
    api_key = "8305fbf269956ad9f4ebacaa7363a875"
