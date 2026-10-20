from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.playwright_spider import PlaywrightSpider
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS


class PrintempsSpider(PlaywrightSpider):
    name = "printemps"
    item_attributes = {"brand": "Printemps", "brand_wikidata": "Q1535260"}
    allowed_domains = ["www.printemps.com"]
    start_urls = ["https://www.printemps.com/ajax/get-stores?location="]
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS | {"ROBOTSTXT_OBEY": False}
    requires_proxy = True

    def parse(self, response: TextResponse) -> Iterable[Feature]:
        for location in response.json()["magasins_lists"]:
            item = Feature(**self.item_attributes)
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
                if day_hours == "00:00-00:00":
                    item["opening_hours"].set_closed(day_name)
                    continue
                for time_range in day_hours.split(" "):
                    item["opening_hours"].add_range(day_name, *time_range.split("-", 1), "%H:%M")
            apply_category(Categories.SHOP_DEPARTMENT_STORE, item)
            yield item
