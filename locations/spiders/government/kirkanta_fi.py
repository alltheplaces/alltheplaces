import re
from collections import Counter
from typing import Any, AsyncIterator, Iterable
from urllib.parse import urlsplit

from scrapy import Spider
from scrapy.exceptions import CloseSpider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.items import Feature, SocialMedia, set_social_media
from locations.licenses import Licenses

# Kirjastohakemisto (Kirkanta), the Finnish Library Database: public, academic
# and special libraries plus archives, via the v3 JSON API. One request returns
# the whole directory. Docs and CC BY 4.0 terms: https://api.kirjastot.fi/
# No opening_hours: schedules need period params and the staffed/self-service
# split has no opening_hours representation.
API_URL = "https://api.kirjastot.fi/v3/library?limit=2000&with=phone_numbers,pictures,links,services"

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

# Hospital patient and school libraries serve restricted populations, as do
# the military academy libraries (Maasotakoulu, Maanpuolustuskorkeakoulu);
# those get access=private rather than a public tag.
ACCESS_PRIVATE_TYPES = {"institutional", "school"}
MILITARY_KEYWORDS = ("sotakoulu", "puolustus")
# Permanently closed units name themselves (single case: the Skanssi desk,
# SULJETTU/CLOSED/STÄNGT in three languages).
CLOSED_TOKENS = re.compile(r"\b(suljettu|closed|stängt)\b", re.IGNORECASE)
# Real libraries the branch_type enum misfiles (single case: Skibban, a
# Swedish-language library in Pori filed as other).
OTHER_INCLUDE = {86797}

# Social handles stamped on many branches (city-system pages) are popped;
# only handles unique to one record are emitted. Persons sections and staff
# contacts stay out (privacy); service blurbs have no OSM vocabulary, except
# the wi-fi template slug which maps to internet_access=wlan.
SOCIAL_DOMAINS = (
    (SocialMedia.FACEBOOK, ("facebook.com",)),
    (SocialMedia.INSTAGRAM, ("instagram.com",)),
    (SocialMedia.YOUTUBE, ("youtube.com", "youtu.be")),
    (SocialMedia.TWITTER, ("twitter.com", "x.com")),
)
WIFI_SLUG = "wi-fi"

FLOOR_TAIL = re.compile(r",\s*(?P<floor>\d+)\.\s*(?:krs|kerros)\.?\s*(?:\([^)]*\))?$", re.IGNORECASE)
FLOOR_PAREN = re.compile(r"\s*\(\s*(?P<floor>\d+)\.\s*(?:krs|kerros)\.?\s*\)$", re.IGNORECASE)
FLOOR_REVERSED = re.compile(r",\s*(?:krs|kerros)\s*(?P<floor>\d+)\.?$", re.IGNORECASE)
FLOOR_PATTERNS = (FLOOR_TAIL, FLOOR_PAREN, FLOOR_REVERSED)


class KirkantaFISpider(Spider):
    name = "kirkanta_fi"
    allowed_domains = ["api.kirjastot.fi"]
    custom_settings = {"DOWNLOAD_TIMEOUT": 60}
    IMAGE_SKIP = ("placeholder", "default", "logo", "brand")
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
            raise CloseSpider(f"no library records from {response.url}")
        candidates = []
        for entry in data["items"]:
            try:
                result = self.parse_entry(entry)
            except Exception:
                ref = entry.get("id") if isinstance(entry, dict) else type(entry).__name__
                self.logger.warning(f"Skipping malformed record {ref}")
                self.crawler.stats.inc_value(f"atp/{self.name}/dropped/error")
                continue
            if result:
                candidates.append(result)
        counts = self.social_counts(candidates)
        # Same place filed under two ids keeps the lowest id either way the
        # feed orders them (single case: Kärkölä 86024/86806). Numeric-aware:
        # plain string comparison misorders mixed-length ids ("10" < "9").
        minima: dict = {}
        for item, place_key, _ in candidates:
            if place_key is None:
                continue
            key = self._ref_key(item["ref"])
            if place_key not in minima or key < minima[place_key][0]:
                minima[place_key] = (key, item["ref"])
        for item, place_key, social in candidates:
            if place_key is not None and item["ref"] != minima[place_key][1]:
                self.crawler.stats.inc_value(f"atp/{self.name}/dropped/duplicate")
                continue
            self.apply_social(item, social, counts)
            yield item

    @staticmethod
    def social_counts(candidates: list) -> Counter:
        counts: Counter = Counter()
        for _, _, social in candidates:
            for network, urls in social.items():
                for url in urls:
                    if key := KirkantaFISpider.social_key(url):
                        counts[key] += 1
        return counts

    def apply_social(self, item: Feature, social: dict, counts: Counter) -> None:
        for network, urls in social.items():
            unique = [u for u in urls if counts.get(self.social_key(u), 0) == 1]
            if unique:
                set_social_media(item, network, unique[0])
                self.crawler.stats.inc_value(f"atp/{self.name}/social/{network.value}")

    @staticmethod
    def _ref_key(ref: str) -> tuple:
        return (0, int(ref)) if ref.isdigit() else (1, ref)

    def parse_entry(self, entry: dict) -> tuple | None:
        if entry.get("id") is None:
            self.logger.warning("Skipping record without id")
            self.crawler.stats.inc_value(f"atp/{self.name}/dropped/no_id")
            return None
        branch_type = entry.get("branch_type")
        self.crawler.stats.inc_value(f"atp/{self.name}/type/{branch_type}")
        names = entry.get("name") or {}
        name_text = " ".join(value for value in names.values() if value).lower()
        if (category := self.category_for(entry, branch_type, name_text)) is None:
            return None

        address = entry.get("address") or {}
        coords = address.get("coordinates") or {}
        try:
            lat, lon = float(coords.get("lat")), float(coords.get("lon"))
        except (TypeError, ValueError):
            if branch_type == "institutional":
                self.logger.warning(f"No coords on {branch_type} {entry.get('id')}")
                self.crawler.stats.inc_value(f"atp/{self.name}/dropped/no_coords")
                return None
            lat, lon = None, None

        name = self.pick_lang(names)
        if not name:
            self.logger.warning(f"No name on {entry.get('id')}")
            self.crawler.stats.inc_value(f"atp/{self.name}/dropped/no_name")
            return None

        item = Feature()
        item["ref"] = str(entry.get("id"))
        apply_category(category, item)
        if access := self.access_for(branch_type, name_text):
            item["extras"]["access"] = access
        item["name"] = name
        self.set_names(item, names, name)

        if lat is not None:
            item["lat"], item["lon"] = lat, lon
        else:
            self.crawler.stats.inc_value(f"atp/{self.name}/emitted/no_coords")

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
        if image := self.pick_image(entry.get("pictures") or []):
            item["image"] = image
        if self.has_wifi(entry.get("services") or []):
            item["extras"]["internet_access"] = "wlan"
            self.crawler.stats.inc_value(f"atp/{self.name}/wifi")

        # Same name, street and town under another id is one place filed twice;
        # the lowest id wins in parse(). Coords stay out of the key: re-surveys
        # metres apart are still one place (Hervanta 86747/86774, ~15 m).
        # Street-less records skip matching: without an address no confident
        # match exists. Resolved name, not fi: distinct sv-fallback names on
        # one street are different places.
        if not street:
            return item, None, self.collect_social(entry)
        return item, (item["name"], street, item.get("city")), self.collect_social(entry)

    def category_for(self, entry: dict, branch_type: str | None, name_text: str) -> Categories | None:
        if CLOSED_TOKENS.search(name_text):
            self.crawler.stats.inc_value(f"atp/{self.name}/dropped/closed")
            return None
        if branch_type in LIBRARY_TYPES or (branch_type == "other" and entry.get("id") in OTHER_INCLUDE):
            return Categories.LIBRARY
        if branch_type == "archive" or (branch_type == "other" and ("arkisto" in name_text or "arkiv" in name_text)):
            return Categories.ARCHIVE
        if branch_type not in ("mobile", "home_service", "other"):
            self.logger.warning(f"Unknown branch_type {branch_type!r} on {entry.get('id')}")
        self.crawler.stats.inc_value(f"atp/{self.name}/dropped/{branch_type}")
        return None

    def access_for(self, branch_type: str | None, name_text: str) -> str | None:
        if branch_type in ACCESS_PRIVATE_TYPES or any(k in name_text for k in MILITARY_KEYWORDS):
            self.crawler.stats.inc_value(f"atp/{self.name}/access/private")
            return "private"
        return None

    @staticmethod
    def set_names(item: Feature, names: dict, name: str) -> None:
        # Translated names keep identity tails; name:fi mirrors the fi name and
        # is never set from a fallback language.
        if names.get("sv") and names["sv"] != name:
            item["extras"]["name:sv"] = names["sv"]
        if names.get("en") and names["en"] != name:
            item["extras"]["name:en"] = names["en"]
        if names.get("fi") and ("name:sv" in item["extras"] or "name:en" in item["extras"]):
            item["extras"]["name:fi"] = name

    @staticmethod
    def collect_social(entry: dict) -> dict:
        social: dict = {}
        links = entry.get("links")
        if not isinstance(links, list):
            return social
        for link in links:
            if not isinstance(link, dict):
                continue
            for url in (link.get("url") or {}).values():
                if not isinstance(url, str):
                    continue
                for network, domains in SOCIAL_DOMAINS:
                    try:
                        host = urlsplit(url.strip()).netloc.lower().split("@")[-1].split(":")[0]
                    except ValueError:
                        continue
                    if any(host == d or host.endswith("." + d) for d in domains):
                        if url not in social.setdefault(network, []):
                            social[network].append(url)
        return social

    @staticmethod
    def social_key(url: str) -> tuple | None:
        try:
            parts = urlsplit(url.strip())
        except ValueError:
            return None
        host = parts.netloc.lower().split("@")[-1].split(":")[0]
        path = parts.path.lower().rstrip("/") or "/"
        for network, domains in SOCIAL_DOMAINS:
            if any(host == d or host.endswith("." + d) for d in domains):
                return network.value, path
        return None

    @staticmethod
    def has_wifi(services: list) -> bool:
        if not isinstance(services, list):
            return False
        for service in services:
            if not isinstance(service, dict):
                continue
            for slug in (service.get("slug") or {}).values():
                if isinstance(slug, str) and WIFI_SLUG in slug:
                    return True
        return False

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
    def pick_image(pictures: list) -> str | None:
        # Per-location building photos; hashes cannot spell the skip words so
        # only human-named logo files match. Default photo first, else first.
        ordered = sorted(pictures, key=lambda p: not p.get("default"))
        for photo in ordered:
            url = (photo.get("files") or {}).get("large") or ""
            if url and not any(s in url.lower() for s in KirkantaFISpider.IMAGE_SKIP):
                return url
        return None

    @staticmethod
    def pick_phone(numbers: list) -> str | None:
        # The phone list also carries email addresses; those stay out, the
        # dedicated email field covers them. First real number wins (the
        # shared Oulu system number is a legitimate branch phone, not a
        # hotline, so no cross-record filtering).
        for row in numbers:
            number = row.get("number") or ""
            if "@" not in number and any(char.isdigit() for char in number):
                return number
        return None
