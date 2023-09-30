from locations.storefinders.stockist import StockistSpider


class AllyFashionAUSpider(StockistSpider):
    name = "ally_fashion_au"
    item_attributes = {"brand": "Ally Fashion", "brand_wikidata": "Q19870623"}
    key = "u13251"

    def parse_item(self, item, location):
        item.pop("website")
        yield item
