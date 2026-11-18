import json
import re
from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.linked_data_parser import LinkedDataParser

# Each visible block states a location's phone below its postcode, which is how the
# one location with no structured data of its own is given a phone number.
PHONE = re.compile(r"(?P<postcode>\d{5})[^(]{0,400}?Phone:\s*(?P<phone>\(\d{3}\)\s*\d{3}-\d{4})")
CLOSED = re.compile(r"Temporarily Closed[^.]{0,200}?(?P<postcode>\d{5})")


class BarrelHouseUSSpider(Spider):
    name = "barrel_house_us"
    item_attributes = {"brand": "Barrel House Bar & Grill"}
    start_urls = ["https://www.barrelhousepub.com/locations"]

    @staticmethod
    def restaurants(response: Response) -> Iterable[dict]:
        """Yield every Restaurant record in the page's structured data."""
        for ld in response.xpath('//script[@type="application/ld+json"]/text()').getall():
            try:
                data = json.loads(ld)
            except json.JSONDecodeError:
                continue
            if isinstance(data, dict) and data.get("@type") == "Restaurant":
                yield data

    def directory(self, response: Response) -> list[dict]:
        """Return the chain directory from the locations page.

        The page carries the chain twice: once with each location's address, phone,
        hours and page, and again as a thinner list of names and addresses alone.
        Only the detailed one is of use, and the thin one would duplicate it.
        """
        for restaurant in self.restaurants(response):
            departments = restaurant.get("department") or []
            if any(department.get("openingHoursSpecification") for department in departments):
                return departments
        return []

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Any]:
        text = " ".join(response.xpath("//text()").getall())
        phones = {match["postcode"]: match["phone"] for match in PHONE.finditer(text)}
        # The fire closure is stated in the page text, immediately above the hours
        # that location nonetheless keeps advertising.
        shut = match["postcode"] if (match := CLOSED.search(text)) else None

        for location in self.directory(response):
            postcode = (location.get("address") or {}).get("postalCode")
            yield response.follow(
                location["url"],
                callback=self.parse_location,
                cb_kwargs={
                    "listed": location,
                    "phone": phones.get(postcode),
                    "shut": postcode is not None and postcode == shut,
                },
            )

    def parse_location(self, response: Response, listed: dict, phone: str | None, shut: bool) -> Iterable[Feature]:
        # A location's own page is the better record: the directory gives one of them
        # an opening time its own page and visible hours both contradict. The closed
        # location is the one with no structured data of its own, so it falls back.
        own = [
            restaurant
            for restaurant in self.restaurants(response)
            if "department" not in restaurant and restaurant.get("address")
        ]
        item = LinkedDataParser.parse_ld(own[0] if own else listed)

        item["ref"] = item["website"] = response.url
        item["branch"] = self.branch(item.pop("name", "") or listed.get("name", ""), item)
        item["phone"] = item.get("phone") or phone
        # The one Facebook page is the chain's own, repeated on every location.
        item["facebook"] = None

        if shut:
            # Shut after a fire, so its advertised hours are not hours it is keeping.
            item["opening_hours"] = None

        apply_category(Categories.RESTAURANT, item)
        item["extras"]["cuisine"] = "burger;pizza"
        yield item

    @staticmethod
    def branch(name: str, item: Feature) -> str | None:
        branch = re.sub(r"^Barrel House\s*[—–-]?\s*", "", name).strip()
        if state := item.get("state"):
            # Two locations repeat their state in the name: "Bloomington IL".
            branch = re.sub(rf"\s+{re.escape(state)}$", "", branch)
        if city := item.get("city"):
            # One name qualifies the branch with its city: "Utica Ridge - Davenport".
            # Only a separated city is dropped, to leave "Downtown Davenport" whole.
            branch = re.sub(rf"\s*[—–-]\s*{re.escape(city)}$", "", branch)
        return branch.strip() or None
