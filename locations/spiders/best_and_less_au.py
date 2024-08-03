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
            item = DictParser.parse(location)
            item["branch"] = item.pop("name")
            item["ref"] = location["address"]["id"]
            item["addr_full"] = location["address"].get("formattedAddress")
            item["street_address"] = clean_address([location["address"].get("line1"), location["address"].get("line2")])
            item["city"] = location["address"].get("town")
            item["state"] = location["address"].get("state")
            item["postcode"] = location["address"].get("postalCode")
            item["phone"] = location["address"].get("phone")
            item["email"] = location["address"].get("email")
            item["website"] = "https://www.bestandless.com.au" + quote(location["url"])
            item["opening_hours"] = OpeningHours()
            for day in location["openingHours"]["weekDayOpeningList"]:
                if day["closed"]:
                    continue
                item["opening_hours"].add_range(
                    day["weekDay"],
                    day["openingTime"]["formattedHour"].upper(),
                    day["closingTime"]["formattedHour"].upper(),
                    "%I:%M %p",
                )
            yield item

        pagination = response.json()["pagination"]
        if pagination["currentPage"] < pagination["totalPages"]:
            yield self.make_request(pagination["currentPage"] + 1)
