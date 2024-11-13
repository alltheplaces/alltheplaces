from typing import Iterable
from urllib.parse import quote

from scrapy import Request, Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import clean_address


class BestAndLessAUSpider(Spider):
    name = "best_and_less_au"
    item_attributes = {"brand": "Best & Less", "brand_wikidata": "Q4896542"}

    def make_request(self, page: int) -> JsonRequest:
        return JsonRequest(
            url="https://prodapi.bestandless.com.au/occ/v2/bnlsite/stores?fields=FULL&currentPage={}".format(page)
        )

    def start_requests(self) -> Iterable[Request]:
        yield self.make_request(0)

    def parse(self, response):
        for location in response.json()["stores"]:
            location.update(location.pop("address"))
            item = DictParser.parse(location)
            item["addr_full"] = location.get("formattedAddress")
            item["street_address"] = clean_address([location.get("line1"), location.get("line2")])
            item["city"] = location.get("town")
            item["state"] = item["state"].get("name")
            item["website"] = "https://www.bestandless.com.au" + quote(location["url"])
            item["opening_hours"] = self.get_opening_hours(location, response.url)
            yield item

        pagination = response.json()["pagination"]
        if pagination["currentPage"] < pagination["totalPages"]:
            yield self.make_request(pagination["currentPage"] + 1)

    def get_opening_hours(self, location, url):
        try:
            o = OpeningHours()
            if opening_hours := location.get("openingHours"):
                for day in opening_hours["weekDayOpeningList"]:
                    if day["closed"]:
                        continue
                    o.add_range(
                        day["weekDay"],
                        day["openingTime"]["formattedHour"].upper(),
                        day["closingTime"]["formattedHour"].upper(),
                        "%I:%M %p",
                    )

            return o.as_opening_hours()
        except Exception as e:
            self.logger.warning(f"Failed to parse opening hours for {url}, {e}")
            self.crawler.stats.inc_value(f"atp/{self.name}/hours/failed")
