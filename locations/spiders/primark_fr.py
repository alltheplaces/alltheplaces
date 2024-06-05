from locations.spiders.penneys_ie import PenneysIESpider
from locations.spiders.primark_gb import PrimarkGBSpider


class PrimarkFRSpider(PenneysIESpider):
    name = "primark_fr"
    item_attributes = PrimarkGBSpider.item_attributes
    locale = "fr-fr"
