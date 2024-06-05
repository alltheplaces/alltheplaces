from locations.spiders.penneys_ie import PenneysIESpider
from locations.spiders.primark_gb import PrimarkGBSpider


class PrimarkBESpider(PenneysIESpider):
    name = "primark_be"
    item_attributes = PrimarkGBSpider.item_attributes
    locale = "nl-be"
