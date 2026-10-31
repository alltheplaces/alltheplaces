import json
import re
from typing import Any, Iterable

import pycountry
from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature


class TonyRomasSpider(Spider):
    name = "tony_romas"
    item_attributes = {"brand": "Tony Roma's", "brand_wikidata": "Q2213883"}
    start_urls = ["https://www.tonyromas.com/locations/"]

    @staticmethod
    def next_data(response: Response) -> dict:
        return json.loads(response.xpath('//script[@id="__NEXT_DATA__"]/text()').get("{}"))

    @staticmethod
    def country_code(name: str | None) -> str | None:
        """Resolve a country as the site names it, such as "USA" or "Curaçao".

        Only exact lookups are used: a fuzzy search resolves "curacao" to the
        Netherlands, which would file that restaurant under the wrong country.
        """
        if not name:
            return None
        for key, value in (
            ("alpha_3", name.upper()),
            ("alpha_2", name.upper()),
            ("name", name),
            ("common_name", name),
            ("official_name", name),
        ):
            try:
                if country := pycountry.countries.get(**{key: value}):
                    return country.alpha_2
            except LookupError:
                continue
        return None

    @staticmethod
    def hours(opening_hours: dict | None) -> OpeningHours:
        oh = OpeningHours()
        for day in DAYS_FULL:
            intervals = (opening_hours or {}).get(day.lower())
            if intervals is None:
                continue
            if not intervals:
                oh.set_closed(day)
                continue
            for interval in intervals:
                opens, closes = interval
                oh.add_range(
                    day,
                    "{hours:02d}:{minutes:02d}".format(**opens),
                    "{hours:02d}:{minutes:02d}".format(**closes),
                )
        return oh

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Any]:
        features = self.next_data(response)["props"]["pageProps"]["locationsData"]["geojson"]["features"]
        for feature in features:
            if feature["properties"].get("coming_soon"):
                continue
            yield response.follow(f"/locations/{feature['properties']['slug']}/", callback=self.parse_location)

    def parse_location(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        location = self.next_data(response)["props"]["pageProps"]["location"]
        address = location.get("address") or {}

        item = Feature()
        item["ref"] = item["website"] = response.url
        item["branch"] = location.get("heading")
        item["street_address"] = address.get("street")
        item["city"] = address.get("city")
        item["state"] = address.get("state")
        # Several Canadian records prefix the postcode with the province's code,
        # which the state field already carries: "AB T5S 1T9".
        item["postcode"] = re.sub(r"^[A-Z]{2}\s+(?=\S+\s)", "", address.get("zip") or "") or None
        item["country"] = self.country_code(address.get("country"))
        item["phone"] = location.get("phone")
        item["email"] = location.get("email")

        if coordinates := location.get("coordinates"):
            item["lon"], item["lat"] = coordinates

        item["opening_hours"] = self.hours(location.get("opening_hours"))

        if not item["country"]:
            self.logger.warning(f"Unresolved country {address.get('country')!r} on {response.url}")

        apply_category(Categories.RESTAURANT, item)
        item["extras"]["cuisine"] = "barbecue;ribs"
        yield item
