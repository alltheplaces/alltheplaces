from locations.storefinders.yext import YextSpider


class BlackSheepCoffeeSpider(YextSpider):
    name = "black_sheep_coffee"
    item_attributes = {"brand": "Black Sheep Coffee", "brand_wikidata": "Q109745011"}
    api_key = "88a4c90cba781a9bee544c96a3f87ff7"
    wanted_types = ["restaurant"]

    def parse_item(self, item, location, **kwargs):
        if item.get("website") is not None:
            item["website"] = item["website"].split("?")[0]  # Strip yext trackers

        yield item
