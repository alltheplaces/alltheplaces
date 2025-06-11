from locations.categories import Categories, apply_category
from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature
from locations.storefinders.storemapper import StoremapperSpider


class BridgeheadCASpider(StoremapperSpider):
    name = "bridgehead_ca"
    item_attributes = {"brand": "Bridgehead", "brand_wikidata": "Q4966509"}
    company_id = "26992-8fhpesVgKnaQ5aIJ"

    def parse_item(self, item: Feature, location: dict):
        item["branch"] = item.pop("name", None)
        item["opening_hours"] = OpeningHours()
        for day_hours in location["store_business_hours"]:
            if day_hours["open_24hrs"] is not None:
                item["opening_hours"].add_range(DAYS_FULL[int(day_hours["week_day"]) - 1], "00:01", "23:59")
            else:
                item["opening_hours"].add_range(
                    DAYS_FULL[int(day_hours["week_day"]) - 1], day_hours["open_time"], day_hours["close_time"]
                )
        apply_category(Categories.COFFEE_SHOP, item)
        yield item
