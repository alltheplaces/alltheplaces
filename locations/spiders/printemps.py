from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours, DAYS_FR
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class PrintempsSpider(JSONBlobSpider):
    name = "printemps"
    item_attributes = {"brand": "Printemps", "brand_wikidata": "Q1535260"}
    allowed_domains = ["www.printemps.com"]
    start_urls = ["https://www.printemps.com/ajax.php?do=magasins&location="]
    locations_key = "magasins_lists"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["lat"] = feature["PR_LAT"]
        item["lon"] = feature["PR_LONG"]
        item["branch"] = feature["PR_LABEL"].removeprefix("Printemps ").removeprefix("Outlet ").removeprefix("outlet ")
        item["street_address"] = feature["PR_ADR"]
        item["city"] = feature["PR_VILLE"]
        item["postcode"] = feature["PR_CP"]
        item["phone"] = feature["TEL_COUNTRY_IND"] + "-" + feature["PHONE"]
        item["image"] = feature["MEDIA_PATH"].split("?", 1)[0]
        item["opening_hours"] = OpeningHours()
        for day_name, day_hours in feature["HORAIRES"].items():
            if day_hours.startswith("Ferm"):
                item["opening_hours"].set_closed(DAYS_FR[day_name.title()])
            else:
                if " " in day_hours:
                    time_ranges = day_hours.split(" ", 1)
                    for time_range in time_ranges:
                        item["opening_hours"].add_range(DAYS_FR[day_name.title()], *time_range.split("-", 1), "%H:%M")
                else:
                    item["opening_hours"].add_range(DAYS_FR[day_name.title()], *day_hours.split("-", 1), "%H:%M")
        apply_category(Categories.SHOP_DEPARTMENT_STORE, item)
        yield item
