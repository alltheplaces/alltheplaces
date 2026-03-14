from locations.storefinders.stockist import StockistSpider


class RoomsToGoUSSpider(StockistSpider):
    name = "rooms_to_go_us"
    item_attributes = {"brand": "Rooms To Go", "brand_wikidata": "Q7366329"}
    key = "u11672"

    def parse_item(self, item, location):
        if "RTG KIDS" in item["name"].upper():
            item["brand"] = "Rooms To Go Kids"
            item["brand_wikidata"] = "Q119443278"
        yield item
