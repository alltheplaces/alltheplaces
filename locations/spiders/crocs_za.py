from locations.spiders.crocs_eu import CrocsEUSpider
from locations.storefinders.stockist import StockistSpider


class CrocsZASpider(StockistSpider):
    name = "crocs_za"
    item_attributes = CrocsEUSpider.item_attributes
    key = "u7310"

    def parse_item(self, item, location, **kwargs):
        for f in location["filters"]:
            if f["name"] == "Crocs Stockist":
                return None
        yield item
