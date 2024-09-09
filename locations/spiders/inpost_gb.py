from typing import Any, Iterable

from scrapy import Request, Spider
from scrapy.http import JsonRequest, Response

from locations.categories import apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class InpostGBSpider(Spider):
    name = "inpost_gb"
    item_attributes = {"name": "InPost", "brand": "InPost", "brand_wikidata": "Q3182097"}
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def make_request(self, page: int) -> JsonRequest:
        return JsonRequest(
            url="https://api-uk-global-points.easypack24.net/v1/points?status=Operating&page={}&per_page=100".format(
                page
            ),
            meta={"page": page},
        )

    def start_requests(self) -> Iterable[Request]:
        yield self.make_request(1)

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["items"]:
            if "parcel_locker" not in location["type"]:
                continue
            item = DictParser.parse(location)
            item["ref"] = item.pop("name")
            item["located_in"] = (
                location["address_details"]["building_number"]
                .removeprefix("24/7 ")
                .removeprefix("InPost Locker")
                .strip(" -")
            )
            item["street_address"] = location["address_details"]["street"]
            item["city"] = location["address_details"]["city"]
            item["postcode"] = location["address_details"]["post_code"]
            item["state"] = location["address_details"]["province"]

            apply_yes_no("indoor", item, location["location_type"] == "Indoor")
            apply_yes_no("parcel_mail_in", item, "parcel_send   " in location["functions"])
            apply_yes_no("parcel_pickup", item, "parcel_collect" in location["functions"])

            if location["location_247"]:
                item["opening_hours"] = "24/7"
            else:
                item["opening_hours"] = self.parse_opening_hours(location["opening_hours"])

            item["website"] = "https://www.inpost.co.uk/lockers/{}".format(item["ref"])

            yield item

        if response.meta["page"] < response.json()["total_pages"]:
            yield self.make_request(response.meta["page"] + 1)

    def parse_opening_hours(self, hours: str) -> OpeningHours:
        oh = OpeningHours()
        for rule in hours.split(";"):
            if not rule:
                continue
            day, times = rule.split("|", 1)
            for time in times.split("|"):
                if time == "-":
                    continue
                oh.add_range(day, *time.split("-"))
        return oh
