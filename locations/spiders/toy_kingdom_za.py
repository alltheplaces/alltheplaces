from locations.storefinders.stockist import StockistSpider


class ToyKingdomZASpider(StockistSpider):
    name = "toy_kingdom_za"
    item_attributes = {
        "brand": "Toy Kingdom",
        "brand_wikidata": "Q130470609",
    }
    key = "u24268"

    def parse_item(self, item, location):
        item.pop("website")
        item["branch"] = item.pop("name")
        yield item
