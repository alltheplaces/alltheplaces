from locations.hours import OpeningHours
from locations.storefinders.stockist import StockistSpider


class LincraftAUSpider(StockistSpider):
    name = "lincraft_au"
    item_attributes = {"brand": "Lincraft", "brand_wikidata": "Q17052417"}
    key = "u6788"

    def parse_item(self, item, location):
        item["website"] = location["custom_fields"][0]["value"].replace("lincraftau.myshopify.com", "lincraft.com.au")
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(location["description"])
        yield item
