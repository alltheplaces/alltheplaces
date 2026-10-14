import re
from typing import Any, AsyncIterator, Iterable

from scrapy import Spider
from scrapy.exceptions import CloseSpider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.licenses import Licenses

# Kirjastohakemisto (Kirkanta), the Finnish Library Database: public, academic
# and special libraries plus archives, via the v3 JSON API. One request returns
# the whole directory. Docs and CC BY 4.0 terms: https://api.kirjastot.fi/
# No opening_hours: schedules need period params and the staffed/self-service
# split has no opening_hours representation.
API_URL = "https://api.kirjastot.fi/v3/library?limit=2000&with=phone_numbers"

# Branch types filed as visitable libraries. Mobiles are excluded (a vehicle at
# a depot address, not an outlet); home_service has no visitable venue; other
# mixes archives with digital-only and art organisations (handled below). The
# feed status (0/1/2) is the live open state from daily schedules, not
# lifecycle, so it is ignored.
LIBRARY_TYPES = {
    "library",
    "main_library",
    "children",
    "polytechnic",
    "university",
    "vocational_college",
    "special",
    "school",
    "institutional",
}

FLOOR_TAIL = re.compile(r",\s*(?P<floor>\d+)\.\s*(?:krs|kerros)\.?\s*(?:\([^)]*\))?$", re.IGNORECASE)
FLOOR_PAREN = re.compile(r"\s*\(\s*(?P<floor>\d+)\.\s*(?:krs|kerros)\.?\s*\)$", re.IGNORECASE)
FLOOR_REVERSED = re.compile(r",\s*(?:krs|kerros)\s*(?P<floor>\d+)\.?$", re.IGNORECASE)
FLOOR_PATTERNS = (FLOOR_TAIL, FLOOR_PAREN, FLOOR_REVERSED)


class KirkantaFISpider(Spider):
    name = "kirkanta_fi"
    allowed_domains = ["api.kirjastot.fi"]
    # API contents CC BY 4.0, attribution required by the v3 terms.
    dataset_attributes = Licenses.CCBY4.value | {
        "source": "api",
        "attribution:name": "Kirjastot.fi",
        "attribution:website": "https://api.kirjastot.fi/",
    }

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(url=API_URL)

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        data = response.json()  # ty: ignore[unresolved-attribute]
        if not data.get("items"):
            raise CloseSpider("no library records")
        for entry in data["items"]:
            if item := self.parse_entry(entry):
                yield item

    def parse_entry(self, entry: dict) -> Feature | None:
        branch_type = entry.get("branch_type")
        self.crawler.stats.inc_value(f"atp/{self.name}/type/{branch_type}")
        names = entry.get("name") or {}
        name_text = " ".join(value for value in names.values() if value).lower()
        if branch_type in LIBRARY_TYPES:
            category = Categories.LIBRARY
        elif branch_type == "archive" or (branch_type == "other" and ("arkisto" in name_text or "arkiv" in name_text)):
            category = Categories.ARCHIVE
        else:
            if branch_type not in ("mobile", "home_service", "other"):
                self.logger.warning(f"Unknown branch_type {branch_type!r} on {entry.get('id')}")
            self.crawler.stats.inc_value(f"atp/{self.name}/dropped/{branch_type}")
            return None

        address = entry.get("address") or {}
        coords = address.get("coordinates") or {}
        if coords.get("lat") is None or coords.get("lon") is None:
            self.logger.warning(f"No coords on {branch_type} {entry.get('id')}")
            self.crawler.stats.inc_value(f"atp/{self.name}/dropped/no_coords")
            return None

        name = self.pick_lang(names)
        if not name:
            self.logger.warning(f"No name on {entry.get('id')}")
            self.crawler.stats.inc_value(f"atp/{self.name}/dropped/no_name")
            return None

        item = Feature()
        item["ref"] = str(entry.get("id"))
        apply_category(category, item)
        item["name"] = name
        # Translated names keep identity tails; name:fi mirrors the fi name and
        # is never set from a fallback language.
        if names.get("sv") and names["sv"] != name:
            item["extras"]["name:sv"] = names["sv"]
        if names.get("en") and names["en"] != name:
            item["extras"]["name:en"] = names["en"]
        if names.get("fi") and ("name:sv" in item["extras"] or "name:en" in item["extras"]):
            item["extras"]["name:fi"] = name

        item["lat"] = float(coords["lat"])
        item["lon"] = float(coords["lon"])

        street = self.pick_lang(address.get("street") or {}) or ""
        street, floor = self.split_floor(street)
        if floor:
            item["extras"]["addr:floor"] = floor
        if street:
            item["street_address"] = street
        # area is the post town, city the municipality; OSM addr:city is the
        # post town, falling back to the municipality where area is empty.
        item["city"] = self.pick_lang(address.get("area") or {}) or self.pick_lang(address.get("city") or {})
        item["postcode"] = address.get("zipcode")
        item["country"] = "FI"

        if phone := self.pick_phone(entry.get("phone_numbers") or []):
            item["phone"] = phone
        if email := self.pick_lang(entry.get("email") or {}):
            item["email"] = email
        if website := self.pick_lang(entry.get("homepage") or {}):
            item["website"] = website
        return item

    @staticmethod
    def split_floor(street: str) -> tuple[str, str | None]:
        # Single unambiguous floor markers only; slash forms stay put (unit
        # numbers are ambiguous) as do ordinal words (zero occurrences here).
        for pattern in FLOOR_PATTERNS:
            if match := pattern.search(street):
                return street[: match.start()], match.group("floor")
        return street, None

    @staticmethod
    def pick_lang(values: dict) -> str | None:
        for lang in ("fi", "sv", "en", "se", "ru"):
            if values.get(lang):
                return values[lang]
        return None

    @staticmethod
    def pick_phone(numbers: list) -> str | None:
        # The phone list also carries email addresses; those stay out, the
        # dedicated email field covers them. First real number wins (the
        # shared Oulu system number is a legitimate branch phone, not a
        # hotline, so no cross-record filtering).
        for entry in numbers:
            number = entry.get("number") or ""
            if "@" not in number and any(char.isdigit() for char in number):
                return number
        return None
