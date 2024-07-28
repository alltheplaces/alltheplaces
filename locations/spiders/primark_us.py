from locations.spiders.penneys_ie import PenneysIESpider
from locations.spiders.primark_gb import PrimarkGBSpider


class PrimarkUSSpider(PenneysIESpider):
    name = "primark_us"
    item_attributes = PrimarkGBSpider.item_attributes
    locale = "en-us"
