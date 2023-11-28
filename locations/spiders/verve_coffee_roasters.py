from locations.storefinders.storepoint import StorepointSpider


class VerveCoffeeRoastersSpider(StorepointSpider):
    name = "verve_coffee_roasters"
    item_attributes = {"brand": "Verve Coffee Roasters", "brand_wikidata": "Q17030230"}
    key = "16254bf8a6deb8"

    def parse_item(self, item, location):
        if location["name"] != "Verve Coffee Roasters":
            # Retailer of coffee beans - ignore.
            return
        yield item
