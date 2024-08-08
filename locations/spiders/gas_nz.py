from locations.categories import Categories, Fuel, apply_category, apply_yes_no
from locations.storefinders.storelocatorwidgets import StoreLocatorWidgetsSpider


class GasNZSpider(StoreLocatorWidgetsSpider):
    name = "gas_nz"
    item_attributes = {"brand": "G.A.S.", "brand_wikidata": "Q112189761"}
    key = "ed66addbfde705ac2e642e1ecd322ccd"

    def parse_item(self, item, location: {}, **kwargs):
        item.pop("website")
        apply_yes_no(Fuel.OCTANE_91, item, "Unleaded 91" in location["filters"])
        apply_yes_no(Fuel.OCTANE_95, item, "Premium 95" in location["filters"])
        apply_yes_no(Fuel.DIESEL, item, "Diesel" in location["filters"])
        apply_category(Categories.FUEL_STATION, item)
        yield item
