import re
from typing import Any, AsyncIterator, Iterable

from scrapy import Spider
from scrapy.http import JsonRequest, TextResponse

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature

LOCKER_NAME_REGEX = re.compile(r"\blockers?\b", re.IGNORECASE)
# Facility type labels are free text set by each library system, so they are
# matched by keyword.
WIFI_LABEL_REGEX = re.compile(r"\bwi-?fi\b|\bwireless internet\b", re.IGNORECASE)
ALL_DAY_CLOSE_TIMES = {"T23:45", "T23:59", "T24:00", "T00:00"}


class BiblioCommonsSpider(Spider):
    """
    BiblioCommons is a catalogue/discovery platform used by many public
    library systems (mostly in the US and Canada). Branch locations are
    available from the BiblioCommons gateway API:
    https://gateway.bibliocommons.com/v2/libraries/<library_id>/locations

    To use this store finder, specify the `library_id` attribute of this
    class. This is the subdomain of the library's BiblioCommons catalogue,
    e.g. "kcls" for https://kcls.bibliocommons.com/.

    Locations are categorised as libraries, except those with "Locker(s)"
    in their name, which are self-service holds pickup lockers and are
    categorised as parcel lockers with `name` set to the API name. A
    location open 00:00-23:45 (or until midnight) every day gets opening
    hours of "24/7".

    For libraries, the API's location name (e.g. "Enumclaw") is stored as
    `branch` and `name` is left unset, as the bare branch name is not the
    name of the library. Subclasses should set `name` in `parse_item` (e.g.
    "Enumclaw Library") following the library system's naming convention.

    Override `parse_item(item, location)` to modify, categorise differently
    or skip (by not yielding) individual locations; `location` is the raw
    location dictionary from the API. Locations that typically need to be
    skipped per library system are bookmobiles, administration/HQ/
    operations buildings, virtual branches, departments inside a branch
    (makerspace, cafe, genealogy room, drive-thru) and non-library partners.
    """

    dataset_attributes: dict = {"source": "api", "api": "bibliocommons.com"}
    library_id: str
    page_size: int = 500  # The API caps larger limits at 500.

    def make_request(self, page: int) -> JsonRequest:
        return JsonRequest(
            url=f"https://gateway.bibliocommons.com/v2/libraries/{self.library_id}/locations?limit={self.page_size}&page={page}",
            cb_kwargs={"page": page},
        )

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield self.make_request(1)

    def parse(self, response: TextResponse, page: int = 1, **kwargs: Any) -> Iterable[Feature | JsonRequest]:
        data = response.json()
        # A page with no results has no "entities" key.
        entities = data.get("entities", {})
        locations = entities.get("locations", {})
        for location_id in data["locations"]["results"]:
            location = locations[location_id]
            if location.get("isHidden"):
                # Hidden locations are not shown in the library's public
                # location list.
                continue
            item = self.parse_location(location, entities)
            yield from self.parse_item(item, location) or []

        if page == 1:
            for next_page in range(2, data["locations"]["pagination"]["pages"] + 1):
                yield self.make_request(next_page)

    def parse_location(self, location: dict, entities: dict) -> Feature:
        item = DictParser.parse(location)
        item["branch"] = item.pop("name")
        item["housenumber"] = (location.get("address") or {}).get("number")
        if centre_point := (location.get("mapLocation") or {}).get("centrePoint"):
            item["lat"] = centre_point.get("lat")
            item["lon"] = centre_point.get("lng")
        item["website"] = location.get("webUrl")
        if image := (entities.get("images") or {}).get(location.get("imageId")):
            item["image"] = image.get("url")

        for contact in location.get("branchContacts") or []:
            if contact.get("contactType") == "phone":
                number = contact.get("globalValue") or contact.get("value")
                if "fax" in (contact.get("label") or "").lower():
                    item["extras"].setdefault(Extras.FAX.value, number)
                elif not item.get("phone"):
                    item["phone"] = number
            elif contact.get("contactType") == "email" and not item.get("email"):
                item["email"] = contact.get("value")

        facility_types = entities.get("facilityTypes") or {}
        for facility in location.get("facilities") or []:
            label = (facility_types.get(facility.get("typeId")) or {}).get("label") or ""
            if WIFI_LABEL_REGEX.search(label):
                apply_yes_no(Extras.WIFI, item, True)

        if self.is_open_24_7(location):
            item["opening_hours"] = "24/7"
        else:
            item["opening_hours"] = self.parse_opening_hours(location)

        if LOCKER_NAME_REGEX.search(item["branch"]):
            item["name"] = item.pop("branch")
            apply_category(Categories.PARCEL_LOCKER, item)
        else:
            apply_category(Categories.LIBRARY, item)
        return item

    @staticmethod
    def is_open_24_7(location: dict) -> bool:
        hours = location.get("hours") or []
        return (
            len(hours) == 7
            and {(rule.get("timeRef") or "").title() for rule in hours} == set(DAYS_FULL)
            and all(rule.get("openTime") == "T00:00" and rule.get("closeTime") in ALL_DAY_CLOSE_TIMES for rule in hours)
        )

    @staticmethod
    def parse_opening_hours(location: dict) -> OpeningHours | None:
        hours = location.get("hours") or []
        if not hours:
            # Typically a location that is temporarily closed, with details
            # only in the free text "hoursNote".
            return None
        oh = OpeningHours()
        for rule in hours:
            if not rule.get("timeRef") or not rule.get("openTime") or not rule.get("closeTime"):
                continue
            oh.add_range(rule["timeRef"], rule["openTime"].removeprefix("T"), rule["closeTime"].removeprefix("T"))
        if not oh:
            return None
        # When weekly hours are given, BiblioCommons (and library websites
        # built on it) display any day without hours as "Closed". Days
        # listed with incomplete times are left unknown.
        listed_days = {(rule.get("timeRef") or "").title() for rule in hours}
        oh.set_closed([day for day in DAYS_FULL if day not in listed_days])
        return oh

    def parse_item(self, item: Feature, location: dict) -> Iterable[Feature]:
        yield item
