from locations.spiders.penneys_ie import PenneysIESpider
from locations.spiders.primark_gb import PrimarkGBSpider


class PrimarkATSpider(PenneysIESpider):
    name = "primark_at"
    item_attributes = PrimarkGBSpider.item_attributes
    locale = "de-at"
