from typing import Any, AsyncIterator, Iterable

from scrapy import Request, Spider
from scrapy.http import JsonRequest, TextResponse

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines
from locations.storefinders.yext_answers import YextAnswersSpider


class YextSearchSpider(Spider):
    dataset_attributes: dict = {"source": "api", "api": "yext"}
    custom_settings: dict = {"ROBOTSTXT_OBEY": False}

    host: str = "https://locator.example-brand.yext-cdn.com"
    page_size: int = 50

    def make_request(self, offset: int) -> JsonRequest:
        return JsonRequest("{}/search?r=250000&per={}&offset={}".format(self.host, self.page_size, offset))

    async def start(self) -> AsyncIterator[Request]:
        yield self.make_request(0)

    def parse(self, response: TextResponse, **kwargs: Any) -> Iterable[Feature | JsonRequest]:
        for location in response.json()["response"]["entities"]:
            item = Feature()
            profile = location["profile"]
            item = DictParser.parse(profile)
            item["ref"] = profile["meta"]["uid"]
            item["branch"] = profile.get("geomodifier")

            item["street_address"] = merge_address_lines(
                [
                    profile["address"]["line1"],
                    profile["address"]["line2"],
                    profile["address"]["line3"],
                ]
            )

            if profile.get("websiteUrl") is not None and "?" in profile.get("websiteUrl"):
                item["website"] = profile.get("websiteUrl", "").split("?", 1)[0]
            else:
                item["website"] = profile.get("websiteUrl")
            if menu_url := profile.get("menuUrl"):
                item["extras"]["website:menu"] = menu_url
            if order_url := profile.get("orderUrl"):
                item["extras"]["website:orders"] = order_url.split("?")[0]

            phones = []
            for phone_type in ["localPhone", "mainPhone", "mobilePhone", "alternatePhone"]:
                phone = profile.get(phone_type)
                if phone:
                    phones.append(phone.get("number"))
            if len(phones) > 0:
                item["phone"] = "; ".join(phones)

            emails = profile.get("emails")
            if emails:
                item["email"] = "; ".join(emails)

            if facebook_vanity := profile.get("facebookVanityUrl"):
                if not facebook_vanity.startswith("http"):
                    item["facebook"] = "https://www.facebook.com/" + facebook_vanity
                else:
                    item["facebook"] = facebook_vanity
            elif facebook_profile := profile.get("facebookPageUrl"):
                item["facebook"] = facebook_profile

            if profile.get("googlePlaceId"):
                item["extras"]["ref:google"] = profile.get("googlePlaceId")

            YextAnswersSpider.parse_payment_methods(profile, item)

            item["opening_hours"] = self.parse_opening_hours(profile.get("hours"))
            if oh := self.parse_opening_hours(profile.get("deliveryHours")).as_opening_hours():
                item["extras"]["opening_hours:delivery"] = oh

            yield from self.parse_item(location, item) or []

        yield from self.request_next_page(response, **kwargs)

    def request_next_page(self, response: TextResponse, **kwargs: Any) -> Iterable[JsonRequest]:
        pager = response.json()["queryParams"]
        offset = int(pager["offset"][0])
        page_size = int(pager["per"][0])
        if offset + page_size < response.json()["response"]["count"]:
            yield self.make_request(offset + page_size)

    def parse_opening_hours(self, hours: dict, **kwargs: Any) -> OpeningHours:
        oh = OpeningHours()
        if not hours:
            return oh
        normal_hours = hours.get("normalHours")
        if not normal_hours:
            return oh
        for day in normal_hours:
            if day.get("isClosed"):
                oh.set_closed(day["day"].title())
            for interval in day.get("intervals", []):
                oh.add_range(day["day"].title(), str(interval["start"]).zfill(4), str(interval["end"]).zfill(4), "%H%M")
        return oh

    def parse_item(self, location: dict, item: Feature) -> Iterable[Feature]:
        yield item
