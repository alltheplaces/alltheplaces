import json
import re
from typing import Any

from scrapy import Request, Spider
from scrapy.http import Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import DAYS, OpeningHours
from locations.items import Feature

URL = "https://www.libertybank.ge/ka/chven-shesakheb/kompaniis-shesakheb/bankomatebi"

# TypeId groups from the map feed. Branches and service centres are banks -- including Liberty
# service points hosted inside Houses of Justice, the Revenue Service, MIA agencies, customs
# posts and prisons (their Title is always a Liberty branch/service-centre label). The two
# "Lombard" pawn services (5, 9) are a separate business and are out of scope.
BRANCH_TYPES = {2, 3, 7, 8, 10, 11, 12, 13, 14, 15}
ATM_TYPES = {1, 6}  # 1 = ATM, 6 = cash-in ATM
PAYMENT_TERMINAL_TYPES = {4}  # LBPay self-service payment terminals

# Georgian and English weekday tokens in WorkingHours -> OpeningHours abbreviation.
DAY_TOKENS = {
    "ორშ": "Mo",
    "სამ": "Tu",
    "ოთხ": "We",
    "ხუთ": "Th",
    "პარ": "Fr",
    "შაბ": "Sa",
    "კვირ": "Su",
    "mon": "Mo",
    "tue": "Tu",
    "wed": "We",
    "thu": "Th",
    "fri": "Fr",
    "sat": "Sa",
    "sun": "Su",
}
# A "Day[ - Day] HH:MM - HH:MM" segment; several are concatenated (sometimes without a
# separator, e.g. "...14:00კვირ 10:00...") so the values are scanned rather than split.
HOURS_RE = re.compile(
    r"({0})\s*(?:-\s*({0})\s*)?(\d{{1,2}}:\d{{2}})\s*-\s*(\d{{1,2}}:\d{{2}})".format("|".join(DAY_TOKENS)),
    re.IGNORECASE,
)


class LibertyBankGESpider(Spider):
    name = "liberty_bank_ge"
    item_attributes = {"brand": "ლიბერთი", "brand_wikidata": "Q6541585"}

    async def start(self) -> Any:
        yield Request(URL)

    def parse(self, response: Response, **kwargs: Any) -> Any:
        # Every location is embedded in the page as `window.pins = [...]`.
        start = response.text.index("[", re.search(r"window\.pins\s*=", response.text).end())
        pins, _ = json.JSONDecoder().raw_decode(response.text, start)

        # The feed lists one pin per *service* (ATM, branch, LBPay, ...) and stacks several at
        # the same coordinates when a site offers more than one. Group by coordinate so each
        # physical location yields a single POI, avoiding duplicate branch/ATM nodes.
        groups: dict[tuple[float, float], list[dict]] = {}
        for pin in pins:
            lat, lon = self.coord(pin["Latitude"]), self.coord(pin["Longitude"])
            if lat is None or lon is None:
                continue  # coordinates are "0" when the location is unknown
            groups.setdefault((round(lat, 5), round(lon, 5)), []).append(pin)

        for members in groups.values():
            types = {pin["TypeId"] for pin in members}
            if types & BRANCH_TYPES:
                primary, kind = self.representative(members, BRANCH_TYPES), "bank"
            elif types & ATM_TYPES:
                primary, kind = self.representative(members, ATM_TYPES), "atm"
            elif types & PAYMENT_TERMINAL_TYPES:
                primary, kind = self.representative(members, PAYMENT_TERMINAL_TYPES), "payment_terminal"
            else:
                continue  # only pawn-shop pins at this site; out of scope

            # Built manually rather than via DictParser: several pins are aggregated into one
            # item, coordinates are comma-decimal strings, Title is the branch label (not the
            # name) and Phone is a shared call centre -- every mapped field would be overridden.
            item = Feature()
            item["ref"] = str(primary["Id"])
            item["lat"] = self.coord(primary["Latitude"])
            item["lon"] = self.coord(primary["Longitude"])
            # NSI supplies name=ლიბერთი for banks; ATMs/terminals have no NSI name. The Title is
            # the specific branch/service-centre label (or the host venue for ATMs/terminals).
            item["branch"] = primary["Title"]
            item["addr_full"] = primary["Address"]
            item["state"] = primary["Location"]  # Georgian administrative region (mkhare), e.g. "იმერეთი"
            if "," in primary["Address"]:
                item["city"] = primary["Address"].split(",", 1)[0].strip()  # Address is "City, street"
            item["opening_hours"] = self.parse_hours(primary)
            # Phone is always the shared 0322 555 500 call centre, never a branch line -> omit.

            if kind == "bank":
                apply_category(Categories.BANK, item)
                apply_yes_no(Extras.ATM, item, bool(types & ATM_TYPES))  # a co-located ATM
            elif kind == "atm":
                apply_category(Categories.ATM, item)
            else:
                apply_category({"amenity": "payment_terminal"}, item)

            yield item

    @staticmethod
    def coord(value: str) -> float | None:
        try:
            number = float(value.replace(",", "."))  # coordinates use a comma decimal separator
        except (AttributeError, ValueError):
            return None
        return number if number != 0 else None

    @staticmethod
    def representative(members: list[dict], types: set[int]) -> dict:
        # Deterministic POI identity: the lowest Id among the winning category's pins.
        return min((pin for pin in members if pin["TypeId"] in types), key=lambda pin: pin["Id"])

    @staticmethod
    def parse_hours(pin: dict) -> str | None:
        if pin.get("IsOpen24Hours") or (pin.get("WorkingHours") or "").strip() == "24/7":
            return "24/7"
        hours = OpeningHours()
        for start, end, open_time, close_time in HOURS_RE.findall(pin.get("WorkingHours") or ""):
            first = DAYS.index(DAY_TOKENS[start.lower()])
            last = DAYS.index(DAY_TOKENS[end.lower()]) if end else first
            for day in DAYS[first : last + 1]:
                hours.add_range(day, open_time, close_time)
        return hours.as_opening_hours() or None
