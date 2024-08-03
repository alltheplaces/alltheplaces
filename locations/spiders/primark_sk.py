from locations.spiders.penneys_ie import PenneysIESpider
from locations.spiders.primark_gb import PrimarkGBSpider


class PrimarkSKSpider(PenneysIESpider):
    name = "primark_sk"
    item_attributes = PrimarkGBSpider.item_attributes
    locale = "sk-sk"
