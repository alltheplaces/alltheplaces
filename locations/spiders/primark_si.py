from locations.spiders.penneys_ie import PenneysIESpider
from locations.spiders.primark_gb import PrimarkGBSpider


class PrimarkSISpider(PenneysIESpider):
    name = "primark_si"
    item_attributes = PrimarkGBSpider.item_attributes
    locale = "sl-si"
