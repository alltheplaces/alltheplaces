from typing import AsyncIterator, Iterable

from scrapy import Spider
from scrapy.http import JsonRequest, TextResponse

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import Feature


class RexelSpider(Spider):
    """
    Rexel (https://www.wikidata.org/wiki/Q962489) is a large multinational company.

    This spider is for all common functionality across subsidiary brands.

    To use, specify:
    - `base_url`: domain name hosting the storefinder, for example,
                  "storefinderapi.example.net"
    - `search_lat`: mandatory paramater, floating point number between -90.0
                    and 90.0
    - `search_lon`: mandatory parameter, floating point number between -180.0
                    and 180.0
    """

    base_url: str = ""
    search_lat: float | None = None
    search_lon: float | None = None

    async def start(self) -> AsyncIterator[JsonRequest]:
        if not self.base_url or self.search_lat is None or self.search_lon is None:
            raise ValueError("base_url, search_lat and search_lon attributes all need to be specified.")
            return
        # This seems to return all stores regardless of lat-long; as long as it's in the right country/area?
        yield JsonRequest(
            url=f"https://{self.base_url}/store-finder/findNearbyStores?latitude={self.search_lat}&longitude={self.search_lon}"
        )

    def parse(self, response: TextResponse) -> Iterable[Feature]:
        for feature in response.json()["results"]:
            feature["address"]["street_address"] = ", ".join(
                filter(
                    None,
                    [
                        feature["address"].pop("line1"),
                        feature["address"].pop("line2"),
                        feature["address"].pop("line3"),
                    ],
                )
            )
            feature["ref"] = feature.pop("name")
            item = DictParser.parse(feature)
            if feature["address"]["phone"] is not None and not feature["address"]["phone"].replace(" ", "").startswith(
                "+443"
            ):
                item["phone"] = feature["address"]["phone"]
            # e.g. https://www.denmans.co.uk/den/Bradley-Stoke-Bristol/store/1AR
            if "address" in feature and "town" in feature["address"] and feature["address"]["town"] is not None:
                item["website"] = (
                    f'https://{self.base_url}/{feature["address"]["town"].replace(" ", "-")}/store/{feature["ref"]}'
                )

            item["opening_hours"] = self.decode_hours(feature)
            # We could also fall back to cartIcon here...
            if feature["storeImages"]:
                store_images = filter(lambda x: (x["format"] == "store" and x["url"]), feature["storeImages"])
                if store_images:
                    item["image"] = next(store_images)["url"]
            yield from self.parse_item(item, feature) or []

    def parse_item(self, item: Feature, feature: dict, **kwargs) -> Iterable[Feature]:
        yield item

    @staticmethod
    def decode_hours(feature: dict) -> OpeningHours:
        oh = OpeningHours()
        if feature["openingHours"] and feature["openingHours"]["rexelWeekDayOpeningList"]:
            for r in filter(lambda x: (not x["closed"]), feature["openingHours"]["rexelWeekDayOpeningList"]):
                oh.add_range(
                    r["weekDay"],
                    r["openingTime"]["formattedHour"],
                    r["closingTime"]["formattedHour"],
                    time_format="%I:%M %p",
                )
        return oh
