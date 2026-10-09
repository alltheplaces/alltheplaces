from datetime import datetime
from typing import AsyncIterator, Iterable

from scrapy.http import JsonRequest, TextResponse

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.user_agents import BROWSER_DEFAULT

GRAPHQL_QUERY = """
query ba_stores($page: Int, $pageSize: Int) {
    ba_stores(currentPage: $page, pageSize: $pageSize) {
        total_count
        items {
            store_id
            is_enabled
            name
            latitude
            longitude
            phone_number
            email_address
            store_address
            store_city
            store_state
            store_zip
            store_country
            sunday_status
            sunday_open
            sunday_close
            monday_status
            monday_open
            monday_close
            tuesday_status
            tuesday_open
            tuesday_close
            wednesday_status
            wednesday_open
            wednesday_close
            thursday_status
            thursday_open
            thursday_close
            friday_status
            friday_open
            friday_close
            saturday_status
            saturday_open
            saturday_close
        }
    }
}
"""

DAYS = ["sunday", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday"]

# The exact time format used by this API could not be confirmed locally
# (Imperva blocks direct requests without a proxy), so try the common ones.
TIME_FORMATS = ["%H:%M:%S", "%H:%M", "%I:%M %p", "%I:%M:%S %p", "%I:%M%p"]

PAGE_SIZE = 500


class BomgaarsUSSpider(JSONBlobSpider):
    name = "bomgaars_us"
    item_attributes = {"brand": "Bomgaars", "brand_wikidata": "Q22059070", "name": "Bomgaars"}
    allowed_domains = ["www.bomgaars.com"]
    requires_proxy = "US"  # Imperva
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(
            url="https://www.bomgaars.com/graphql",
            method="POST",
            data={"query": GRAPHQL_QUERY, "variables": {"page": 1, "pageSize": PAGE_SIZE}},
            headers={
                "Origin": "https://www.bomgaars.com",
                "Referer": "https://www.bomgaars.com/storelocator/",
                "X-Requested-With": "XMLHttpRequest",
            },
        )

    def extract_json(self, response: TextResponse) -> list[dict]:
        stores = response.json()["data"]["ba_stores"]
        items = stores["items"]
        if stores.get("total_count", 0) > len(items):
            self.logger.error(
                "total_count %s exceeds page size %s, results are truncated", stores["total_count"], PAGE_SIZE
            )
        return items

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        if not feature.get("is_enabled"):
            return

        item["branch"] = item.pop("name", None)
        apply_category(Categories.SHOP_COUNTRY_STORE, item)

        item["opening_hours"] = OpeningHours()
        for day in DAYS:
            if not feature.get(f"{day}_status"):
                continue
            open_time = self.parse_time(feature.get(f"{day}_open"))
            close_time = self.parse_time(feature.get(f"{day}_close"))
            if open_time and close_time:
                item["opening_hours"].add_range(day.title(), open_time, close_time)

        yield item

    @staticmethod
    def parse_time(value: str) -> str | None:
        if not value:
            return None
        for time_format in TIME_FORMATS:
            try:
                return datetime.strptime(value.strip(), time_format).strftime("%H:%M")
            except ValueError:
                continue
        return None
