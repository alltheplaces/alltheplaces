from locations.spiders.five_guys import FiveGuysSpider
from locations.storefinders.yext import YextSpider


# YextSpider applies to countries: DE, ES, FR, GB
# Refer to FiveGuysSpider for other countries.
class FiveGuysYextSpider(YextSpider):
    name = "five_guys_yext"
    item_attributes = FiveGuysSpider.item_attributes
    api_key = "8305fbf269956ad9f4ebacaa7363a875"
