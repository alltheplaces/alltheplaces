from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.storefinders.stockist import StockistSpider


class AftersIceCreamUSSpider(StockistSpider):
    name = "afters_ice_cream_us"
    item_attributes = {"brand": "Afters Ice Cream", "brand_wikidata": "Q119264038"}
    key = "u8301"

    def parse_item(self, item, location):
        item.pop("email")
        item.pop("website")
        hours_string = location["description"].replace("Hours |", "")
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(hours_string)

        apply_category(Categories.ICE_CREAM, item)

        yield item
