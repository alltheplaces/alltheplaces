from locations.categories import Categories, apply_category
from locations.storefinders.stockist import StockistSpider


class AlivePharmacyWarehouseAUSpider(StockistSpider):
    name = "alive_pharmacy_warehouse_au"
    item_attributes = {"brand": "Alive Pharmacy Warehouse", "brand_wikidata": "Q119258489"}
    key = "u6442"

    def parse_item(self, item, location):
        item.pop("website")
        apply_category(Categories.PHARMACY, item)
        yield item
