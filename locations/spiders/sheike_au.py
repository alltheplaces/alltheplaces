from locations.hours import DAYS_EN, OpeningHours
from locations.storefinders.stockist import StockistSpider


class SheikeAUSpider(StockistSpider):
    name = "sheike_au"
    item_attributes = {"brand": "SHEIKE", "brand_wikidata": "Q117747877"}
    key = "u5720"

    def parse_item(self, item, location):
        hours_string = ""
        for day_hours in location["custom_fields"]:
            if day_hours["name"] not in DAYS_EN:
                continue
            hours_string = f"{hours_string} " + day_hours["name"] + ": " + day_hours["value"]
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(hours_string)
        yield item
