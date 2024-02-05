from typing import Any
from urllib.parse import urljoin

from scrapy import Spider
from scrapy.http import Response

from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature


class WorldFinanceUSSpider(Spider):
    name = "world_finance_us"
    item_attributes = {"brand": "World Finance", "brand_wikidata": "Q3569971"}
    start_urls = ["https://world-finance-api.vercel.app/api/branch-data"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json().values():
            if location["_archived"] or location["_draft"]:
                continue
            item = Feature()
            item["ref"] = location["name"]
            item["lat"] = location["latitude"]
            item["lon"] = location["longitude"]
            item["website"] = urljoin("https://www.loansbyworld.com/branches/", location["slug"])
            item["phone"] = location["phone"]
            item["addr_full"] = location["address"]
            item["street_address"] = location["address-line-1"]
            item["extras"]["add:unit"] = location["address-line-2"]
            item["city"] = location["city"]
            item["state"] = location["state"]
            item["postcode"] = location["zip-code"]

            item["opening_hours"] = OpeningHours()
            for day in DAYS_FULL:
                if time := location["{}-hours".format(day.lower())]:
                    if time == "Closed":
                        continue
                    item["opening_hours"].add_range(day, *time.split("-"), time_format="%I:%M%p")

            yield item
