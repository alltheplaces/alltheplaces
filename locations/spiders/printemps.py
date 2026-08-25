import json
import re
from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.hours import DAYS_FR, OpeningHours
from locations.items import Feature
from locations.playwright_spider import PlaywrightSpider
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS


class PrintempsSpider(PlaywrightSpider):
    name = "printemps"
    item_attributes = {"brand": "Printemps", "brand_wikidata": "Q1535260"}
    allowed_domains = ["www.printemps.com"]
    start_urls = ["https://www.printemps.com/ajax/get-stores?location="]
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS
    requires_proxy = True

    def parse(self, response: TextResponse) -> Iterable[Feature]:
        for location in json.loads(response.xpath("//pre//text()").get())["magasins_lists"]:
            item = Feature()
            item["ref"] = location["ID"]
            item["lat"] = location["PR_LAT"]
            item["lon"] = location["PR_LONG"]
            item["branch"] = (
                location["PR_LABEL"].removeprefix("Printemps ").removeprefix("Outlet ").removeprefix("outlet ")
            )
            item["street_address"] = location["PR_ADR"]
            item["city"] = location["PR_VILLE"]
            item["postcode"] = location["PR_CP"]
            item["phone"] = location["TEL_COUNTRY_IND"] + "-" + location["PHONE"]
            item["image"] = location["MEDIA_PATH"].split("?", 1)[0]
            item["website"] = location["URL"]
            item["opening_hours"] = OpeningHours()
            for day_name, day_hours in location["HORAIRES"].items():
                day_hours = re.sub(r"(?<![\d:])(\d{1,2})\s*-\s*(\d{1,2})(?![\d:])", r"\1:00-\2:00", day_hours)
                if day_hours.startswith("Ferm"):
                    item["opening_hours"].set_closed(DAYS_FR[day_name.title()])
                else:
                    if " " in day_hours:
                        time_ranges = day_hours.split(" ", 1)
                        for time_range in time_ranges:
                            item["opening_hours"].add_range(day_name.title(), *time_range.split("-", 1), "%H:%M")
                    else:
                        item["opening_hours"].add_range(day_name.title(), *day_hours.split("-", 1), "%H:%M")
            apply_category(Categories.SHOP_DEPARTMENT_STORE, item)
            yield item
