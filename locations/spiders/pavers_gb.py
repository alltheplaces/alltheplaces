from typing import Any, Iterable

from scrapy import Request, Spider
from scrapy.http import JsonRequest, Response

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import merge_address_lines


class PaversGBSpider(Spider):
    name = "pavers_gb"
    item_attributes = {
        "brand": "Pavers",
        "brand_wikidata": "Q7155843",
        "country": "GB",
    }
    allowed_domains = ["pavers.co.uk"]

    def make_request(self, page: int) -> JsonRequest:
        return JsonRequest(
            url="https://www.pavers.co.uk/api/storeLocation/search?query&page={}".format(page), meta={"page": page}
        )

    def start_requests(self) -> Iterable[Request]:
        yield self.make_request(1)

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["result"]["response"]["results"]:
            item = DictParser.parse(location["data"])
            if isinstance(item["website"], dict):
                item["website"] = None

            item["street_address"] = merge_address_lines(
                [location["data"]["address"]["line1"], location["data"]["address"].get("line2")]
            )

            hours = OpeningHours()
            for day, intervals in location["data"]["hours"].items():
                if not isinstance(intervals, dict):
                    continue
                if intervals.get("isClosed") is True:
                    hours.set_closed(day)
                    continue
                for interval in intervals["openIntervals"]:
                    hours.add_range(day, interval["start"], interval["end"])
            item["opening_hours"] = hours
            yield item
        if len(response.json()["result"]["response"]["results"]) == 20:
            yield self.make_request(response.meta["page"] + 1)
