from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.storefinders.stockist import StockistSpider


class WoodsCoffeeUSSpider(StockistSpider):
    name = "woods_coffee_us"
    item_attributes = {"brand": "Woods Coffee", "brand_wikidata": "Q8033255"}
    key = "u11293"

    def parse_item(self, item, location):
        hours_string = location["description"].upper().replace("DAILY", "MON-SUN").replace("\n", " ")
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(hours_string)
        apply_category(Categories.COFFEE_SHOP, item)
        yield item
