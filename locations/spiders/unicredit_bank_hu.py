import re
from typing import Any, AsyncIterator
from urllib.parse import urlencode

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import DAYS_HU, OpeningHours, sanitise_day


class UnicreditBankHUSpider(Spider):
    name = "unicredit_bank_hu"
    item_attributes = {"brand": "UniCredit", "brand_wikidata": "Q45568"}

    # Shared UniCredit group locator (also used by the unicreditbank.hu branch finder iframe).
    # getMarkersFiltered returns branches and ATMs inside a map bounding box, but the server
    # collapses dense areas to at most ~99 markers. We therefore walk the country as a quadtree:
    # a cell that comes back at/above SPLIT_THRESHOLD is subdivided until every leaf is complete.
    API = "https://group.unicreditbanking.net/branch/markerService/getMarkersFiltered"
    COUNTRY_BBOX = (45.6, 16.0, 48.7, 23.0)  # (sw_lat, sw_lng, ne_lat, ne_lng) covering Hungary
    SPLIT_THRESHOLD = 90  # complete responses observed up to ~95; truncation plateaus at ~99
    MIN_SPAN = 0.02  # stop subdividing below this span (degrees) to guarantee termination

    async def start(self) -> AsyncIterator[Any]:
        yield self._cell_request(self.COUNTRY_BBOX)

    def _cell_request(self, bbox: tuple[float, float, float, float]) -> JsonRequest:
        sw_lat, sw_lng, ne_lat, ne_lng = bbox
        params = {
            "country": "HU",
            "lang": "hu",
            "mandant": "hu",
            "globalFilter": 3,  # default filter: returns both branches and ATMs
            "localFilter": "",
            "showGroupLocations": "false",  # Hungarian locations only, no cross-border group POIs
            "swLat": sw_lat,
            "swLng": sw_lng,
            "neLat": ne_lat,
            "neLng": ne_lng,
            "zoomLevel": 13,
        }
        return JsonRequest(url="{}?{}".format(self.API, urlencode(params)), cb_kwargs={"bbox": bbox})

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
        item.pop("phone", None)  # every branch reports the same central call-centre number

        self.parse_address(item, location.get("address"))
        if opening_hours := self.parse_hours(location.get("workinghours")):
            item["opening_hours"] = opening_hours

        # "attributes" is a slash-delimited set of feature codes (see markerService/getFilters):
        # "accessibility" = barrier-free branch; "01"/"04"/"05" = deposit-capable ("befizetős") ATM.
        attributes = {code for code in (location.get("attributes") or "").split("/") if code}

        if location.get("type") == "branch":
            item["branch"] = item.pop("name", None)
            apply_yes_no(Extras.WHEELCHAIR, item, "accessibility" in attributes)
            apply_yes_no(Extras.ATM, item, location.get("bankomat") is True)  # branch has an on-site ATM
            apply_category(Categories.BANK, item)
        elif location.get("type") == "atm":
            if item.get("name"):
                # Keep the source display label but drop the deposit/withdrawal service suffix
                # ("... (Kifizetés)" / "... (Be/kifizetés)"), which is already captured by cash_in.
                item["name"] = (
                    re.sub(r"\s*\([^)]*kifizetés[^)]*\)", "", item["name"], flags=re.IGNORECASE).strip() or None
                )
            apply_yes_no(Extras.CASH_IN, item, bool(attributes & {"01", "04", "05"}))
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
        if match := re.match(r"(\d{4})\s+(.+?)\.?$", lines[-1]):  # last line is always "<postcode> <city>"
            item["postcode"], item["city"] = match.group(1), match.group(2)
            lines = lines[:-1]
        # Drop temporary-relocation notices ("Felújítás miatt ... érhető el."); a trailing landmark
        # line (e.g. shopping centre / public building) is not a street and is not kept.
        lines = [line for line in lines if "Felújítás" not in line]
        if lines:
            item["street_address"] = lines[0]

    def parse_hours(self, workinghours: list | None) -> OpeningHours | None:
        if not isinstance(workinghours, list) or not workinghours:
            return None
        opening_hours = OpeningHours()
        # Flat list in groups of five per day: [day_name, open, close, open2, close2].
        for i in range(0, len(workinghours) - 4, 5):
            if not (day := sanitise_day(workinghours[i], DAYS_HU)):
                continue
            if workinghours[i + 1] and workinghours[i + 2]:
                opening_hours.add_range(day, workinghours[i + 1], workinghours[i + 2])
            if workinghours[i + 3] and workinghours[i + 4]:
                opening_hours.add_range(day, workinghours[i + 3], workinghours[i + 4])
        return opening_hours or None
