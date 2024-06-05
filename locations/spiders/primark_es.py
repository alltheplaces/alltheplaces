from locations.spiders.penneys_ie import PenneysIESpider
from locations.spiders.primark_gb import PrimarkGBSpider


class PrimarkESSpider(PenneysIESpider):
    name = "primark_es"
    item_attributes = PrimarkGBSpider.item_attributes
    locale = "es-es"
