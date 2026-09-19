import json
from typing import Any, AsyncIterator

import scrapy
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours, day_range, sanitise_day
from locations.items import Feature

GRAPHQL_QUERY = """
query GetAllStores($filter: StoreAttributeFilterInput, $pageSize: Int = 100, $currentPage: Int = 1) {
    stores(filter: $filter, pageSize: $pageSize, currentPage: $currentPage) {
        items {
            id
            name
            latitude
            longitude
            link
            image
            recurring_hours
            address
            city
            country_id
            region_code
            postcode
            phone
            email
        }
    }
}
"""


class RunningsUSSpider(scrapy.Spider):
    name = "runnings_us"
    item_attributes = {"brand": "Runnings", "brand_wikidata": "Q125924536", "name": "Runnings"}

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(
            url="https://www.runnings.com/graphql",
            data={
                "query": GRAPHQL_QUERY,
                "variables": {"filter": {"country_id": {"eq": "US"}}, "pageSize": 200, "currentPage": 1},
            },
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json()["data"]["stores"]["items"]:
            item = Feature()
            item["ref"] = str(store["id"])
            item["branch"] = store["name"]
            item["lat"] = store["latitude"]
            item["lon"] = store["longitude"]
            item["street_address"] = store["address"]
            item["city"] = store["city"]
            item["state"] = store["region_code"]
            item["postcode"] = store["postcode"]
            item["country"] = store["country_id"]
            item["phone"] = store["phone"]
            item["email"] = store["email"]
            item["website"] = "https://www.runnings.com/storelocator/store/" + store["link"]

            if store.get("image") and "logo" not in store["image"].lower():
                item["image"] = "https://www.runnings.com/media/" + store["image"]

            # Recurring hours also include separate "Firearms ..." ranges (for
            # gun sales only, not general store hours) and occasional one-off
            # holiday closures, neither of which are weekly opening hours.
            item["opening_hours"] = OpeningHours()
            for entry in json.loads(store["recurring_hours"] or "[]"):
                name = entry.get("name", "")
                if "firearm" in name.lower() or "closed" in name.lower():
                    continue
                if "-" in name:
                    start_day, _, end_day = name.partition("-")
                    days = day_range(start_day, end_day)
                else:
                    day = sanitise_day(name)
                    days = [day] if day else []
                for day in days:
                    item["opening_hours"].add_range(day, entry["start_time"], entry["end_time"], "%I:%M %p")

            apply_category(Categories.SHOP_DEPARTMENT_STORE, item)

            yield item
