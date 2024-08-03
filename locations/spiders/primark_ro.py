from locations.spiders.penneys_ie import PenneysIESpider
from locations.spiders.primark_gb import PrimarkGBSpider


class PrimarkROSpider(PenneysIESpider):
    name = "primark_ro"
    item_attributes = PrimarkGBSpider.item_attributes
    locale = "ro-ro"
