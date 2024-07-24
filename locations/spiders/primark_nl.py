from locations.spiders.penneys_ie import PenneysIESpider
from locations.spiders.primark_gb import PrimarkGBSpider


class PrimarkNLSpider(PenneysIESpider):
    name = "primark_nl"
    item_attributes = PrimarkGBSpider.item_attributes
    locale = "nl-nl"
