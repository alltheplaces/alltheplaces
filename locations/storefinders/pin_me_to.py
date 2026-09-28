from typing import Any, AsyncIterator, Iterable

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import PaymentMethods, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import Feature


class PinMeToSpider(Spider):
    dataset_attributes: dict = {"source": "api", "api": "public.pinmeto.com"}

    id: str
    key: str

    async def start(self) -> AsyncIterator[Any]:
        yield JsonRequest("https://public.pinmeto.com/api/v1/{}/{}/locations".format(self.id, self.key))

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["locations"]:
            self.pre_process_data(location)

            item = DictParser.parse(location)
            item["street_address"] = item.pop("street", None)
            item["branch"] = location.get("locationDescriptor")
            item["extras"]["start_date"] = location.get("openingDate")

            if payment_methods := location.get("paymentMethods"):
                apply_yes_no(PaymentMethods.CREDIT_CARDS, item, "creditCard" in payment_methods)
                apply_yes_no(PaymentMethods.DEBIT_CARDS, item, "debitCard" in payment_methods)
                apply_yes_no(PaymentMethods.CONTACTLESS, item, "nfc" in payment_methods)

            yield from self.post_process_item(item, response, location) or []

    def parse_opening_hours(self, location: dict) -> OpeningHours:
        oh = OpeningHours()
        for day, rule in ((location.get("hours") or {}).get("openHours") or {}).items():
            if rule["state"] != "Open":
                raise Exception(rule)
            for time in rule["span"]:
                oh.add_range(day, time["open"], time["close"])
        return oh

    def pre_process_data(self, location: dict, **kwargs) -> None:
        """Override with any pre-processing on the item."""

    def post_process_item(self, item: Feature, response: Response, location: dict, **kwargs) -> Iterable[Feature]:
        """Override with any post-processing on the item."""
        yield item
