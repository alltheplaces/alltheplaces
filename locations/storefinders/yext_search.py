from typing import Any, Iterable

from scrapy import Request, Spider
from scrapy.http import JsonRequest, Response

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines
from locations.storefinders.yext_answers import YextAnswersSpider


class YextSearchSpider(Spider):
    dataset_attributes = {"source": "api", "api": "yext"}
    custom_settings = {"ROBOTSTXT_OBEY": False}

    host: str = "https://locator.chick-fil-a.com.yext-cdn.com"
    page_size: int = 50

    def make_request(self, offset: int) -> JsonRequest:
        return JsonRequest("{}/search?r=250000&per={}&offset={}".format(self.host, self.page_size, offset))

    def start_requests(self) -> Iterable[Request]:
        yield self.make_request(0)

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["response"]["entities"]:
            item = Feature()
            location = location["profile"]
            item = DictParser.parse(location)
            item["ref"] = location["meta"]["uid"]
            item["branch"] = location.get("geomodifier")

            item["street_address"] = merge_address_lines(
                [
                    location["address"]["line1"],
                    location["address"]["line2"],
                    location["address"]["line3"],
                ]
            )

            if location.get("websiteUrl") is not None and "?" in location.get("websiteUrl"):
                item["website"] = location.get("websiteUrl", "").split("?", 1)[0]
            else:
                item["website"] = location.get("websiteUrl")
            item["extras"]["website:menu"] = location.get("menuUrl")
            item["extras"]["website:orders"] = location.get("orderUrl")

            phones = []
            for phone_type in ["localPhone", "mainPhone", "mobilePhone"]:
                phone = location.get(phone_type)
                if phone:
                    phones.append(phone.get("number"))
            if len(phones) > 0:
                item["phone"] = "; ".join(phones)

            emails = location.get("emails")
            if emails:
                item["email"] = "; ".join(emails)

            item["facebook"] = location.get("facebookPageUrl")

            if location.get("googlePlaceId"):
                item["extras"]["ref:google"] = location.get("googlePlaceId")

            YextAnswersSpider.parse_payment_methods(self, location, item)

            item["opening_hours"] = self.parse_opening_hours(location.get("hours"))
            item["extras"]["opening_hours:delivery"] = self.parse_opening_hours(location.get("deliveryHours")).as_opening_hours()

            yield from self.parse_item(location, item) or []

        yield from self.request_next_page(response, **kwargs)

    def request_next_page(self, response: Response, **kwargs: Any) -> Any:
        pager = response.json()["queryParams"]
        offset = int(pager["offset"][0])
        page_size = int(pager["per"][0])
        if offset + page_size < response.json()["response"]["count"]:
            yield self.make_request(offset + page_size)

    def parse_opening_hours(self, hours: dict, **kwargs: Any) -> OpeningHours | None:
        oh = OpeningHours()
        if not hours:
            return None
        normal_hours = hours.get("normalHours")
        if not normal_hours:
            return None
        for day in normal_hours:
            if day.get("isClosed"):
                oh.set_closed(day["day"].title())
            for interval in day.get("intervals", []):
                oh.add_range(day["day"].title(), str(interval["start"]).zfill(4), str(interval["end"]).zfill(4), "%H%M")
        return oh

    def parse_item(self, location: dict, item: Feature) -> Iterable[Feature]:
        yield item
