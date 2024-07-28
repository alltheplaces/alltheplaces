from typing import Any, Iterable
from urllib.parse import urlencode

import scrapy
from scrapy import Request
from scrapy.http import JsonRequest, Response

from locations.hours import DAYS_NL, OpeningHours, sanitise_day
from locations.items import Feature


class KruidvatSpider(scrapy.Spider):
    name = "kruidvat"
    item_attributes = {"brand": "Kruidvat", "brand_wikidata": "Q2226366"}
    allowed_domains = ["kruidvat.nl"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def make_request(self, api: str, page: int) -> JsonRequest:
        return JsonRequest(
            url="{}?{}".format(
                api, urlencode({"fields": "FULL", "radius": "100000", "pageSize": "100", "currentPage": str(page)})
            ),
            meta={"api": api, "page": page},
        )

    def start_requests(self) -> Iterable[Request]:
        yield self.make_request("https://www.kruidvat.be/api/v2/kvb/stores", 0)
        yield self.make_request("https://www.kruidvat.nl/api/v2/kvn/stores", 0)

    def parse(self, response: Response, **kwargs: Any) -> Any:
        pagination = response.json()["pagination"]
        if pagination["currentPage"] < pagination["totalPages"]:
            yield self.make_request(response.meta["api"], pagination["currentPage"] + 1)

        for store in response.json().get("stores"):
            oh = OpeningHours()
            for day in store.get("openingHours", {}).get("weekDayOpeningList"):
                oh.add_range(
                    day=sanitise_day(day.get("weekDay")[:2], DAYS_NL),
                    open_time=day.get("openingTime", {}).get("formattedHour"),
                    close_time=day.get("closingTime", {}).get("formattedHour"),
                )

            properties = {
                "ref": store.get("externalId"),
                "addr_full": store.get("address", {}).get("formattedAddress"),
                "street_address": store.get("address", {}).get("line1"),
                "country": store.get("address", {}).get("country").get("isocode"),
                "city": store.get("address").get("town"),
                "state": store["address"].get("province"),
                "postcode": store.get("address", {}).get("postalCode"),
                "lat": store.get("geoPoint", {}).get("latitude"),
                "lon": store.get("geoPoint", {}).get("longitude"),
                "website": response.urljoin(store.get("url")),
                "opening_hours": oh.as_opening_hours(),
            }

            yield Feature(**properties)
