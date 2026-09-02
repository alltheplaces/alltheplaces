import re
from typing import Any, AsyncIterator
from urllib.parse import urlencode

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours

# The generic branch call-centre line, present on the large majority of branch records instead
# of a branch-specific number. Compared digits-only since raw formatting varies.
NATIONAL_HOTLINE_DIGITS = "421269202096"

# Titles that are just the generic Slovak word for "branch"/"ATM" rather than anything
# location-specific (e.g. a mall or host business name), so keeping them as name/branch would
# add no information beyond the category tag already applied.
GENERIC_TITLES = {"pobočka", "bankomat"}

DAY_CODES = {"MO": "Mo", "TU": "Tu", "WE": "We", "TH": "Th", "FR": "Fr", "SA": "Sa", "SU": "Su"}


class UnicreditBankSKSpider(Spider):
    name = "unicredit_bank_sk"
    item_attributes = {"brand": "UniCredit", "brand_wikidata": "Q45568"}

    # Shared UniCredit group locator (also used by the unicreditbank.sk branch finder iframe).
    # getMarkersFiltered returns branches and ATMs inside a map bounding box, but the server
    # collapses dense areas to at most ~99 markers. We therefore walk the country as a quadtree:
    # a cell that comes back at/above SPLIT_THRESHOLD is subdivided until every leaf is complete.
    API = "https://group.unicreditbanking.net/branch/markerService/getMarkersFiltered"
    COUNTRY_BBOX = (47.5, 16.7, 49.7, 22.7)  # (sw_lat, sw_lng, ne_lat, ne_lng) covering Slovakia
    SPLIT_THRESHOLD = 90  # complete responses observed up to ~95; truncation plateaus at ~99
    MIN_SPAN = 0.02  # stop subdividing below this span (degrees) to guarantee termination

    async def start(self) -> AsyncIterator[Any]:
        yield self._cell_request(self.COUNTRY_BBOX)

    def _cell_request(self, bbox: tuple[float, float, float, float]) -> JsonRequest:
        sw_lat, sw_lng, ne_lat, ne_lng = bbox
        params = {
            "country": "SK",
            "lang": "en",
            "mandant": "sk",
            "globalFilter": 3,  # default filter: returns both branches and ATMs
            "localFilter": "",
            "showGroupLocations": "false",  # Slovak locations only, no cross-border group POIs
            "swLat": sw_lat,
            "swLng": sw_lng,
            "neLat": ne_lat,
            "neLng": ne_lng,
            "zoomLevel": 13,
        }
        return JsonRequest(
            url="{}?{}".format(self.API, urlencode(params)),
            headers={"Referer": "https://www.unicreditbank.sk/"},
            cb_kwargs={"bbox": bbox},
        )

    def parse(self, response: Response, bbox: tuple[float, float, float, float], **kwargs: Any) -> Any:
        locations = response.json()
        sw_lat, sw_lng, ne_lat, ne_lng = bbox

        if (
            len(locations) >= self.SPLIT_THRESHOLD
            and (ne_lat - sw_lat) > self.MIN_SPAN
            and (ne_lng - sw_lng) > self.MIN_SPAN
        ):
            mid_lat, mid_lng = (sw_lat + ne_lat) / 2, (sw_lng + ne_lng) / 2
            for sub_bbox in (
                (sw_lat, sw_lng, mid_lat, mid_lng),
                (sw_lat, mid_lng, mid_lat, ne_lng),
                (mid_lat, sw_lng, ne_lat, mid_lng),
                (mid_lat, mid_lng, ne_lat, ne_lng),
            ):
                yield self._cell_request(sub_bbox)
            return

        if len(locations) >= self.SPLIT_THRESHOLD:
            self.logger.warning("Cell {} hit the marker cap at minimum span; results may be truncated".format(bbox))

        for location in locations:
            if item := self.parse_location(location):
                yield item

    def parse_location(self, location: dict) -> Any:
        item = DictParser.parse(location)
        item["ref"] = str(location["id"])
        item["lat"] = location.get("locLat")
        item["lon"] = location.get("locLng")
        item["phone"] = location.get("phoneNo")

        if (item.get("name") or "").strip().lower() in GENERIC_TITLES:
            item.pop("name", None)

        if item.get("phone") and re.sub(r"\D", "", item["phone"]) == NATIONAL_HOTLINE_DIGITS:
            item["phone"] = None

        # faxNo is identical to phoneNo on every branch record observed; it is not a genuine
        # separate fax line, so it is not worth surfacing as an extra.

        self.parse_address(item, location.get("address"))
        if opening_hours := self.parse_hours(location.get("workinghours")):
            item["opening_hours"] = opening_hours

        attributes = {code for code in (location.get("attributes") or "").split("/") if code}

        if location.get("type") == "branch":
            item["branch"] = item.pop("name", None)
            apply_yes_no(Extras.ATM, item, location.get("bankomat") is True)
            apply_category(Categories.BANK, item)
        elif location.get("type") == "atm":
            # "DEPOZIT ATM" (deposit ATM) marks a cash-in capable machine.
            apply_yes_no(Extras.CASH_IN, item, "DEPOZIT ATM" in attributes)
            apply_category(Categories.ATM, item)
        else:
            self.logger.error("Unexpected location type: {}".format(location.get("type")))
            return None

        return item

    def parse_address(self, item: dict, address: str | None) -> None:
        item.pop("addr_full", None)  # HTML blob; parsed into components below
        if not address:
            return
        lines = [line.strip() for line in re.split(r"<br\s*/?>", address) if line.strip()]
        if not lines:
            return
        # Last line is usually "<postcode> <city>", but a large share of records omit the
        # postcode and give just the city.
        last = lines[-1]
        if match := re.match(r"^([\d\s]{3,8}\d)\s+(.+?)\.?$", last):
            item["postcode"], item["city"] = match.group(1).strip(), match.group(2)
        else:
            item["city"] = last.rstrip(".")
        lines = lines[:-1]
        if lines:
            item["street_address"] = lines[0]

    def parse_hours(self, workinghours: list | None) -> OpeningHours | None:
        if not isinstance(workinghours, list) or not workinghours:
            return None
        opening_hours = OpeningHours()
        # Flat list in groups of five per day: [day_code, open, close, open2, close2].
        for i in range(0, len(workinghours) - 4, 5):
            if not (day := DAY_CODES.get(workinghours[i])):
                continue
            if workinghours[i + 1] and workinghours[i + 2]:
                opening_hours.add_range(day, workinghours[i + 1], workinghours[i + 2])
            if workinghours[i + 3] and workinghours[i + 4]:
                opening_hours.add_range(day, workinghours[i + 3], workinghours[i + 4])
        return opening_hours or None
