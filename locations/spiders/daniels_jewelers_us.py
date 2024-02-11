from locations.hours import OpeningHours
from locations.storefinders.stockist import StockistSpider


class DanielsJewelersUSSpider(StockistSpider):
    name = "daniels_jewelers_us"
    item_attributes = {"brand": "Daniel's Jewelers", "brand_wikidata": "Q120763875"}
    key = "u15600"

    def parse_item(self, item, location):
        for custom_field in location.get("custom_fields"):
            if custom_field["id"] == 6307:
                item["ref"] = custom_field["value"]
            elif custom_field["id"] == 5350:
                item["opening_hours"] = OpeningHours()
                item["opening_hours"].add_ranges_from_string(custom_field["value"])
        yield item
