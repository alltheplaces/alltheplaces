from locations.hours import DAYS_FULL, OpeningHours
from locations.storefinders.where2getit import Where2GetItSpider


class DdsDiscountsUSSpider(Where2GetItSpider):
    name = "dds_discounts_us"
    item_attributes = {
        "brand_wikidata": "Q83743863",
        "brand": "dd's Discounts",
    }
    api_brand_name = "ddsdiscounts"
    api_key = "4E0CC702-70E5-11E8-923C-16F58D89CD5A"

    def parse_item(self, item, location):
        item["branch"] = location["name1"]
        item["state"] = location["state"] or location["province"]
        item["lat"] = location["latitude"]
        item["lon"] = location["longitude"]

        oh = OpeningHours()
        for day in DAYS_FULL:
            if hours := location.get(day.lower()):
                if hours == "Closed":
                    oh.set_closed(day)
                elif " - " in hours:
                    oh.add_range(day, *hours.split(" - "), time_format="%I:%M %p")
                else:
                    self.logger.error(f"Unknown hours format: {hours!r}")
        item["opening_hours"] = oh

        yield item
