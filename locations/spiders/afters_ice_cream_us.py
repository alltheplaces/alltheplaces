from locations.hours import OpeningHours
from locations.storefinders.stockist import StockistSpider


class AftersIceCreamUSSpider(StockistSpider):
    name = "afters_ice_cream_us"
    item_attributes = {
        "brand": "Afters Ice Cream",
        "brand_wikidata": "Q119264038",
        "extras": {"shop": "ice_cream"},
    }
    key = "u8301"

    def parse_item(self, item, location):
        item.pop("email")
        item.pop("website")
        hours_string = location["description"].replace("Hours |", "")
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(hours_string)
        yield item
