from locations.spiders.penneys_ie import PenneysIESpider
from locations.spiders.primark_gb import PrimarkGBSpider


class PrimarkITSpider(PenneysIESpider):
    name = "primark_it"
    item_attributes = PrimarkGBSpider.item_attributes
    locale = "it-it"
