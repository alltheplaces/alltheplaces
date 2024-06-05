from locations.spiders.penneys_ie import PenneysIESpider
from locations.spiders.primark_gb import PrimarkGBSpider


class PrimarkCZSpider(PenneysIESpider):
    name = "primark_cz"
    item_attributes = PrimarkGBSpider.item_attributes
    locale = "cs-cz"
