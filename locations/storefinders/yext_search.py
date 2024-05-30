from typing import Any, Iterable

from scrapy import Request, Spider
from scrapy.http import JsonRequest, Response

from locations.categories import PaymentMethods, apply_yes_no
from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


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

            item["ref"] = location["url"]
            item["name"] = location["profile"]["name"]

            item["street_address"] = merge_address_lines(
                [
                    location["profile"]["address"]["line1"],
                    location["profile"]["address"]["line2"],
                    location["profile"]["address"]["line3"],
                ]
            )
            item["city"] = location["profile"]["address"]["city"]
            item["state"] = location["profile"]["address"]["region"]
            item["country"] = location["profile"]["address"]["countryCode"]
            item["postcode"] = location["profile"]["address"]["postalCode"]

            coords = location["profile"].get("displayCoordinate") or location["profile"].get("yextDisplayCoordinate")
            item["lat"] = coords["lat"]
            item["lon"] = coords["long"]

            item["website"] = location["profile"].get("websiteUrl", "").split("?", 1)[0]

            emails = location["profile"].get("emails")
            if emails:
                item["email"] = emails[0]

            item["facebook"] = location["profile"].get("facebookPageUrl")

            if location["profile"].get("googlePlaceId"):
                item["extras"]["ref:google"] = location["profile"].get("googlePlaceId")

            if payment_methods := location["profile"].get("paymentOptions"):
                apply_yes_no(PaymentMethods.CASH, item, "Cash" in payment_methods, False)
                apply_yes_no(PaymentMethods.CHEQUE, item, "Check" in payment_methods, False)
                apply_yes_no(PaymentMethods.MASTER_CARD, item, "MasterCard" in payment_methods, False)
                apply_yes_no(PaymentMethods.VISA, item, "Visa" in payment_methods, False)
                apply_yes_no(PaymentMethods.AMERICAN_EXPRESS, item, "American Express" in payment_methods, False)
                apply_yes_no(PaymentMethods.DISCOVER_CARD, item, "Discover" in payment_methods, False)

            item["opening_hours"] = self.parse_opening_hours(location)

            yield from self.parse_item(location, item) or []

        pager = response.json()["queryParams"]
        offset = int(pager["offset"][0])
        page_size = int(pager["per"][0])
        if offset + page_size < response.json()["response"]["count"]:
            yield self.make_request(offset + page_size)

    def parse_opening_hours(self, location: dict, **kwargs: Any) -> OpeningHours | None:
        oh = OpeningHours()
        hours = location["profile"].get("hours")
        if not hours:
            return None
        normal_hours = hours.get("normalHours")
        if not normal_hours:
            return None
        for day in normal_hours:
            if day.get("isClosed"):
                continue
            for interval in day.get("intervals", []):
                oh.add_range(day["day"].title(), str(interval["start"]).zfill(4), str(interval["end"]).zfill(4), "%H%M")
        return oh

    def parse_item(self, location: dict, item: Feature) -> Iterable[Feature]:
        yield item
