from locations.storefinders.storepoint import StorepointSpider


class TheYardMilkshakeBarUSSpider(StorepointSpider):
    name = "the_yard_milkshake_bar_us"
    item_attributes = {"brand": "The Yard Milkshake Bar", "brand_wikidata": "Q116737896"}
    key = "16185477881cab"

    def parse_item(self, item, location: {}, **kwargs):
        if item["email"] is not None:
            if "@" not in item["email"]:
                item.pop("email")
        yield item
