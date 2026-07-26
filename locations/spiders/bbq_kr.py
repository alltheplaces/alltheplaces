from typing import Any, AsyncIterator
from urllib.parse import quote

from scrapy import Request, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_WEEKDAY, DAYS_WEEKEND, OpeningHours
from locations.items import Feature

NAME_INDEX_URL = "https://bbq.co.kr/api/delivery/family/list?page={}&size=2000"
SEARCH_URL = "https://bbq.co.kr/api/delivery/family/search/by-name/{}?page={}&size=2000"

# The locator has no bulk endpoint: branches can only be listed by a substring
# search on their name, or ten at a time by proximity to a coordinate. Almost
# every name ends in "점" (branch), so searching for that alone returns the bulk
# of the network in two requests. Completeness does not rest on that convention
# though - the name index is the authority on which branches exist, and any name
# without the term is searched for individually, so an unconventionally named
# branch costs one extra request rather than being missed.
BULK_SEARCH_TERM = "점"


class BbqKRSpider(Spider):
    name = "bbq_kr"
    item_attributes = {"brand": "BBQ치킨", "brand_wikidata": "Q87716489"}

    async def start(self) -> AsyncIterator[Request]:
        yield Request(
            NAME_INDEX_URL.format(1),
            callback=self.parse_name_index,
            cb_kwargs={"page": 1, "names": set()},
        )

    def parse_name_index(self, response: Response, page: int, names: set[str]) -> Any:
        data = response.json()
        names.update(entry["familyName"] for entry in data["content"] if entry.get("familyName"))

        if not data["last"]:
            yield Request(
                NAME_INDEX_URL.format(page + 1),
                callback=self.parse_name_index,
                cb_kwargs={"page": page + 1, "names": names},
            )
            return

        for term in [BULK_SEARCH_TERM, *sorted(name for name in names if BULK_SEARCH_TERM not in name)]:
            yield self.search_request(term, 1)

    def search_request(self, term: str, page: int) -> Request:
        return Request(
            SEARCH_URL.format(quote(term), page),
            callback=self.parse_search,
            cb_kwargs={"term": term, "page": page},
        )

    def parse_search(self, response: Response, term: str, page: int) -> Any:
        data = response.json()

        for store in data["content"]:
            # Note that "isNowActive" does not report whether a branch exists: a
            # third of them are flagged inactive at any moment, including ones
            # whose own published hours say they are open, so it appears to track
            # some transient online ordering state and is deliberately ignored.
            if "테스트" in store["familyName"]:
                continue  # In-house test records, several with plausible coordinates
            item = Feature()
            item["ref"] = store["branchId"]
            item["branch"] = store["familyName"]
            item["addr_full"] = store["address"]
            if not self.is_placeholder_phone(store["tel"]):
                item["phone"] = store["tel"]
            item["lat"] = store["latitude"]
            item["lon"] = store["longitude"]

            if hours := self.parse_opening_hours(store.get("openSchedule") or {}):
                item["opening_hours"] = hours

            apply_category(Categories.RESTAURANT, item)

            yield item

        if not data["last"]:
            yield self.search_request(term, page + 1)

    @staticmethod
    def is_placeholder_phone(tel: str) -> bool:
        # Some branches carry an unfilled area code with an all-zero local
        # number, e.g. "02-0000-0000" or "033-000-0000" (the digit count after
        # the area code varies), rather than leaving the field blank.
        parts = tel.split("-")
        return len(parts) >= 2 and all(part.strip("0") == "" for part in parts[1:])

    @staticmethod
    def parse_opening_hours(schedule: dict) -> OpeningHours | None:
        # TODO: "closeScheduleList" and "tempCloseSchedule" carry regular and
        # temporary closures, but every sampled branch left both empty.
        ranges = [
            (DAYS_WEEKDAY, schedule.get("weekdayOpenAt"), schedule.get("weekdayCloseAt")),
            (DAYS_WEEKEND, schedule.get("weekendOpenAt"), schedule.get("weekendCloseAt")),
        ]
        oh = OpeningHours()
        for days, open_time, close_time in ranges:
            if open_time and close_time:
                oh.add_days_range(days, open_time, close_time)
        return oh if oh.as_opening_hours() else None