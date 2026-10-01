from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import merge_address_lines


class DrMartensSpider(Spider):
    name = "dr_martens"
    item_attributes = {"brand": "Dr. Martens", "brand_wikidata": "Q1126126"}
    custom_settings = {"ROBOTSTXT_OBEY": False}
    no_refs = True
    attempt_after_empty_response = 0

    def make_request(self, page: int) -> JsonRequest:
        return JsonRequest(
            url="https://www.drmartens.com/api/stores/search",
            data={"market": "en_GB", "latitude": 55.860149, "longitude": -4.254456, "page": page},
            cb_kwargs=dict(page=page),
        )

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield self.make_request(0)

    def parse(self, response: Response, page: int) -> Any:
        results = response.json()
        for location in results.get("stores", []):
            if location.get("ownStore") is False:  # Skip retail stores or stockists
                continue
            location.update(location.pop("address", {}))
            item = DictParser.parse(location)
            location["street_address"] = merge_address_lines([location.get("line1"), location.get("line2")])
            #  location["displayName"] is inconsistent to clean and set as branch
            item.pop("name")
            apply_category(Categories.SHOP_SHOES, item)
            if opening_hours := location.get("openingHours"):
                try:
                    oh = OpeningHours()
                    for day, times in opening_hours.items():
                        start_time, end_time = times.split("-")
                        oh.add_range(day, start_time.strip(), end_time.strip())
                    item["opening_hours"] = oh
                except Exception as e:
                    self.logger.error(f"Failed to parse opening hours: {opening_hours}, {e}")
            yield item

        next_page = results.get("cursor")
        # The API sometimes returns an empty stores list for a page (e.g. page 10) and
        # then resumes with data on a later page (e.g. page 11). To be safe, don't
        # stop at the first empty page: keep trying page + 1 and give up only after
        # three consecutive empty responses.
        if next_page is not None:
            self.attempt_after_empty_response = 0  # reset: only consecutive failures count
            yield self.make_request(int(next_page))
        elif self.attempt_after_empty_response < 3:
            self.attempt_after_empty_response += 1
            yield self.make_request(page + 1)
