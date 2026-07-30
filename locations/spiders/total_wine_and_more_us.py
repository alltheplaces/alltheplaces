from typing import Any, AsyncIterator, Iterable

import pycountry
from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.geo import city_locations
from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class TotalWineAndMoreUSSpider(Spider):
    name = "total_wine_and_more_us"
    item_attributes = {"brand": "Total Wine", "brand_wikidata": "Q7828084"}
    allowed_domains = ["www.totalwine.com"]

    def make_request(self, query: str, state: str | None = None) -> JsonRequest:
        return JsonRequest(
            url="https://www.totalwine.com/registry/~actions/GET_STORES/location-slideout-component/",
            data={"query": query},
            meta={"query": query, "state": state},
        )

    async def start(self) -> AsyncIterator[JsonRequest]:
        for subdivision in pycountry.subdivisions.get(country_code="US"):
            yield self.make_request(subdivision.name, subdivision.code.removeprefix("US-"))

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature | JsonRequest]:
        stores = DictParser.get_nested_key(response.json(), "stores") or []

        pagination = DictParser.get_nested_key(response.json(), "pagination") or {}
        if state := response.meta["state"]:
            if pagination.get("totalResults", 0) > len(stores):
                # The API returns at most 40 stores per query, so refine by city.
                for city in city_locations("US", 100000):
                    if city["admin1code"] == state:
                        yield self.make_request("{}, {}".format(city["name"], response.meta["query"]))

        for location in stores:
            item = DictParser.parse(location)
            item["ref"] = location["storeNumber"]
            item["branch"] = item.pop("name")
            item["street_address"] = clean_address([location.get("address1"), location.get("address2")])
            item["website"] = "https://www.totalwine.com/store-info/" + item["ref"]

            apply_yes_no(Extras.WIFI, item, location["wifiAvailable"], False)

            if location["storeHours"]["hasHours"]:
                item["opening_hours"] = OpeningHours()
                for day_hours in location["storeHours"]["days"]:
                    if day_hours["closedStatus"]:
                        item["opening_hours"].set_closed(day_hours["dayOfWeek"].title())
                    else:
                        item["opening_hours"].add_range(
                            day_hours["dayOfWeek"].title(),
                            day_hours["openingTime"],
                            day_hours["closingTime"],
                            "%I:%M %p",
                        )

            apply_category(Categories.SHOP_ALCOHOL, item)
            yield item
