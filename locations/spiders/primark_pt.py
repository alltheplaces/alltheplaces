from locations.spiders.penneys_ie import PenneysIESpider
from locations.spiders.primark_gb import PrimarkGBSpider


class PrimarkPTSpider(PenneysIESpider):
    name = "primark_pt"
    item_attributes = PrimarkGBSpider.item_attributes
    locale = "pt-pt"
