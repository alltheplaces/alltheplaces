from locations.spiders.forever_new_au_nz import FOREVER_NEW_SHARED_ATTRIBUTES
from locations.storefinders.stockist import StockistSpider


class ForeverNewZASpider(StockistSpider):
    name = "forever_new_za"
    item_attributes = FOREVER_NEW_SHARED_ATTRIBUTES
    key = "u7737"

    def parse_item(self, item, location):
        item.pop("website")
        yield item
