import json
from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature

FINDER = "https://www.amf.com/bowlero-location/finder?_format=json"
# The brands the operator runs its centres under, and the names it gives them.
#
# The brand the feed states beside a centre is no longer the centre's own. It
# calls 152 centres named "Bowlero" Lucky Strike, three named "AMF" the same,
# and ten named "Bowl America" Bowlero, and the one centre still trading as
# Bowlmor is in among the Lucky Strikes. What a centre is named is what it
# trades as, so the name is read instead.
BRANDS = [
    ("Lucky Strike", {"brand": "Lucky Strike"}),
    ("Bowlmor", {"brand": "Bowlmor Lanes", "brand_wikidata": "Q4951260"}),
    ("Bowlero", {"brand": "Bowlero", "brand_wikidata": "Q17102967"}),
    ("AMF", {"brand": "AMF Bowling Center", "brand_wikidata": "Q4652616"}),
]
# A day the centre keeps shut, and a centre shut until further notice.
SHUT = "closed"
SUSPENDED = "temporarily closed"


class AmfBowlingSpider(Spider):
    """Every bowling centre the operator runs, from the finder its sites share.

    The operator has been renamed twice over - Bowlmor AMF, then Bowlero, then
    Lucky Strike Entertainment - and its centres trade under four of its names
    besides three dozen that keep names of their own. The finder answers for
    all of them at once, whichever of the sites it is asked through.
    """

    name = "amf_bowling"
    allowed_domains = ["www.amf.com"]
    start_urls = [FINDER]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        for location in json.loads(response.body):
            named = (location.get("name") or "").strip()
            if self.suspended(location):
                self.logger.info(f"{named} is temporarily closed, so it is not published")
                continue

            item = Feature(
                ref=location["id"],
                street_address=location["address1"],
                lat=location["lat"],
                lon=location["lng"],
                city=location["city"],
                state=location["state"],
                postcode=location["zip"],
                # Two of the centres are in Ontario, and without the country
                # the feed states for them their province does not survive.
                country=location.get("country") or "US",
                phone=location["phone"],
                website=location["url"],
            )

            for trading_as, brand in BRANDS:
                if named.casefold().startswith(trading_as.casefold()):
                    item.update(brand)
                    # What is left of the name is the place the centre stands in.
                    item["branch"] = named.removeprefix(trading_as).strip(" -") or None
                    break
            else:
                item["name"] = named or None

            item["opening_hours"] = self.parse_hours(location)

            apply_category(Categories.BOWLING, item)

            yield item

    def parse_hours(self, location: dict) -> OpeningHours:
        oh = OpeningHours()
        for day in self.stated_days(location):
            opens, closes = (self.first(day, part) for part in ("startTime", "endTime"))
            if opens.casefold() == SHUT:
                oh.set_closed(day.get("label"))
                continue
            if not opens or not closes:
                continue
            try:
                oh.add_range(day.get("label"), opens, closes, time_format="%I:%M %p")
            except ValueError:
                self.logger.warning(f"Unparsed hours {opens!r} to {closes!r} at {location.get('name')}")
        return oh

    def suspended(self, location: dict) -> bool:
        """Say whether the centre is shut until further notice.

        Fifteen of them say so against every day of the week, and none says so
        against only some, so a centre saying it of the whole week is not open
        for business and is not published.
        """
        if not (days := self.stated_days(location)):
            return False
        return all(SUSPENDED in self.first(day, "startTime").casefold() for day in days)

    @staticmethod
    def stated_days(location: dict) -> list[dict]:
        return [day for stated in (location.get("hours") or []) for day in (stated.get("hours") or [])]

    @staticmethod
    def first(day: dict, part: str) -> str:
        """Return the one time the feed states for a day, which it states as a list."""
        stated = day.get(part) or [None]
        return (stated[0] or "").strip()
