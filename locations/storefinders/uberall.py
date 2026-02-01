from typing import AsyncIterator, Iterable

from scrapy import Spider
from scrapy.http import JsonRequest, TextResponse

from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours
from locations.items import Feature


class UberallSpider(Spider):
    """
    Uberall provides a web based store locator.
    https://uberall.com/en-us/products/locator-local-pages

    Use by specifying the `key`, and optional filtering via `business_id_filter`
    """

    dataset_attributes: dict = {"source": "api", "api": "uberall.com"}

    key: str
    business_id_filter: int | None = None

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(url=f"https://uberall.com/api/storefinders/{self.key}/locations/all")

    def parse(self, response: TextResponse) -> Iterable[Feature]:
        if response.json()["status"] != "SUCCESS":
            self.logger.warning("Request failed")

        for feature in response.json()["response"]["locations"]:
            self.pre_process_data(feature)
            if self.business_id_filter:
                if feature["businessId"] != self.business_id_filter:
                    continue

            feature["street_address"] = ", ".join(filter(None, [feature["streetAndNumber"], feature["addressExtra"]]))
            feature["ref"] = feature.get("identifier")

            item = DictParser.parse(feature)

            item["image"] = ";".join(filter(None, [p.get("publicUrl") for p in feature["photos"] or []]))

            oh = OpeningHours()
            for rule in feature["openingHours"]:
                if rule.get("closed"):
                    continue
                # I've only seen from1 and from2, but I guess it could any length
                for i in range(1, 3):
                    if rule.get(f"from{i}") and rule.get(f"to{i}"):
                        oh.add_range(
                            DAYS[rule["dayOfWeek"] - 1],
                            rule[f"from{i}"],
                            rule[f"to{i}"],
                        )
            item["opening_hours"] = oh

            yield from self.post_process_item(item, response, feature)

    def post_process_item(self, item: Feature, response: TextResponse, location: dict) -> Iterable[Feature]:
        """Override with any post-processing on the item."""
        yield item

    def pre_process_data(self, location: dict, **kwargs) -> None:
        """Override with any pre-processing on the item."""
