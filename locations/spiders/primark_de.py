from locations.spiders.penneys_ie import PenneysIESpider
from locations.spiders.primark_gb import PrimarkGBSpider


class PrimarkDESpider(PenneysIESpider):
    name = "primark_de"
    item_attributes = PrimarkGBSpider.item_attributes
    locale = "de-de"
