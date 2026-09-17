import re
from typing import Any, AsyncIterator, Iterable

from scrapy import Spider
from scrapy.http import JsonRequest, Request, TextResponse

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature

LOCKER_NAME_REGEX = re.compile(r"\blockers?\b", re.IGNORECASE)
# Facility type labels are free text set by each library system, so they are
# matched by keyword.
WIFI_LABEL_REGEX = re.compile(r"\bwi-?fi\b|\bwireless internet\b", re.IGNORECASE)
ALL_DAY_CLOSE_TIMES = {"T23:45", "T23:59", "T24:00", "T00:00"}
UNIT_REGEX = re.compile(
    r"(.+?)[\s,]+((?:suites?|ste\.|ste|unit|room|bldg|building|no\.)(?=[\s.#\d])[\s.]*.+|#\s*\S+)", re.IGNORECASE
)
REDIRECTED_PHONE_REGEX = re.compile(r"answered at|please call", re.IGNORECASE)
CLOSED_NOTE_REGEX = re.compile(r"\bclosed?\b|\bclosure\b", re.IGNORECASE)


class BiblioCommonsSpider(Spider):
    """
    BiblioCommons is a library catalogue and website platform used by many
    public library systems, mostly in the US and Canada. Its gateway API
    lists a library system's locations.
    https://www.bibliocommons.com/

    To use, specify:
      - `library_id`: the catalogue subdomain, e.g. "kcls" for
        https://kcls.bibliocommons.com/

    The location name is stored as `branch`, and subclasses should set
    `name`. Locations named "Locker(s)" are categorised as parcel lockers
    and keep the API name. Override `parse_item(item, location)` to modify
    or skip locations (e.g. bookmobiles, offices, departments inside a
    branch), or to yield a request for the branch web page carrying the item
    in `cb_kwargs`.

    A location without hours whose name or hours note says it is closed gets
    "Mo-Su closed", the ATP convention for a temporary closure; mark
    permanently closed locations with `set_closed`.
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

    def parse(self, response: TextResponse, page: int, **kwargs: Any) -> Iterable[Feature | Request]:
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
        if street := item.get("street"):
            # e.g. "NE 8th Street, Suite K-11", "N. Oracle Rd., #199"
            if m := UNIT_REGEX.fullmatch(street):
                item["street"], item["unit"] = m.group(1), m.group(2)
            item["street"] = item["street"].strip(" ,")
        if centre_point := (location.get("mapLocation") or {}).get("centrePoint"):
            item["lat"] = centre_point.get("lat")
            item["lon"] = centre_point.get("lng")
        item["website"] = location.get("webUrl")
        if image := (entities.get("images") or {}).get(location.get("imageId")):
            item["image"] = image.get("url")

        for contact in location.get("branchContacts") or []:
            if contact.get("contactType") == "phone":
                number = contact.get("globalValue") or contact.get("value")
                label = (contact.get("label") or "").lower()
                if REDIRECTED_PHONE_REGEX.search(label):
                    # e.g. "Calls answered at Burien Library during Burien
                    # open hours": another location's number.
                    continue
                if "fax" in label:
                    item["extras"].setdefault(Extras.FAX.value, number)
                elif re.search(r"\b(?:text|sms)\b", label):
                    item["extras"].setdefault("contact:sms", number)
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
        oh = OpeningHours()
        if not hours:
            # A location without hours that says it is closed (e.g. "Closed
            # for renovation." in "hoursNote", or "Arvada Library (Closed
            # for Redesign)") is temporarily closed, which ATP expresses as
            # "Mo-Su closed". Other locations without hours are unknown.
            if CLOSED_NOTE_REGEX.search("{} {}".format(location.get("name") or "", location.get("hoursNote") or "")):
                oh.set_closed(DAYS_FULL)
                return oh
            return None
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

    def parse_item(self, item: Feature, location: dict) -> Iterable[Feature | Request]:
        yield item
