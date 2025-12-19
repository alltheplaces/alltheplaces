from locations.storefinders.storepoint import StorepointSpider


class BoosterJuiceUSCASpider(StorepointSpider):
    name = "booster_juice_us_ca"
    item_attributes = {"brand": "Booster Juice", "brand_wikidata": "Q4943796"}
    key = "16608a967359e1"

    def parse_item(self, item, location):
        item["branch"] = item.pop("name")
        yield item
