from typing import Any, Iterable

from scrapy import Request, Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import set_closed


class DeutscheTelekomDESpider(Spider):
    name = "deutsche_telekom_de"
    item_attributes = {
        "brand": "Deutsche Telekom",
        "brand_wikidata": "Q9396",
        "extras": Categories.SHOP_MOBILE_PHONE.value,
    }

    def make_request(self, page: int) -> JsonRequest:
        return JsonRequest(url="https://shopseite.telekom.de/api/shops?_page={}".format(page))

    def start_requests(self) -> Iterable[Request]:
        yield self.make_request(1)

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["data"]:
            if location["type"] != "tsg":
                # Seems type = "ivs" are not branded locations.
                # Also kind = "pa", "tp", "ts"?
                continue

            item = DictParser.parse(location)
            item["lat"] = location["address"]["latitude"]
            item["lon"] = location["address"]["longitude"]
            item["housenumber"] = location["address"]["street_number"]
            item["image"] = location["images"]["original"]
            item["website"] = location["properties"]["store_url"]

            item["opening_hours"] = OpeningHours()
            for day, times in location["opening_times"]["opening_hours"].items():
                for time in times:
                    item["opening_hours"].add_range(day, time[0], time[1])

            item["extras"]["start_date"] = location["properties"]["initial_opening_date"]
            if location["closed"]:
                set_closed(item)

            yield item

        paginator = response.json()["meta"]
        if paginator["current_page"] < paginator["total_pages"]:
            yield self.make_request(paginator["current_page"] + 1)
    drop_attributes = {"image"}
