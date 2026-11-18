import json
import re
from typing import AsyncIterator, Iterable
from urllib.parse import urlencode

from scrapy import Spider
from scrapy.exceptions import CloseSpider
from scrapy.http import Request, Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import DAYS_FI, OpeningHours
from locations.items import Feature

# No Wikidata QID or NSI entry exists for Pakettipiste (checked 2026-10-15), so no wikidata tags.
BRAND = "Pakettipiste"
OPERATOR = {"brand": BRAND, "operator": BRAND}

# Lokaatio prefixes: indoor/outdoor lockers vs manned pickup counters.
LOCKER_PREFIXES = ("Sisäautomaatti ", "Ulkoautomaatti ")
PICKUP_PREFIX = "Noutopiste "
# Sijoituspaikka must agree with the Lokaatio kind; mismatches are counted but Lokaatio still rules.
PLACEMENT_BY_KIND = {"Sisäautomaatti": "Sisällä", "Ulkoautomaatti": "Ulkona", "Noutopiste": "MSP"}
MANNED_LABEL = "Miehitetty noutopiste"  # Type restatement, not placement info.

DAY_FIELDS = ("Maanantai", "Tiistai", "Keskiviikko", "Torstai", "Perjantai", "Lauantai", "Sunnuntai")
RANGE_RE = re.compile(r"(\d{1,2}):(\d{2})-(\d{1,2}):(\d{2})")
HREF_RE = re.compile(r'href="([^"]+)"')


class PakettipisteFISpider(Spider):
    name = "pakettipiste_fi"

    # The map's ArcGIS layer returns Esri JSON only (no GeoJSON), so the shared finder is unusable.
    API_URL = "https://services6.arcgis.com/EO9b2HZRu3Zun6mk/arcgis/rest/services/Haku_2/FeatureServer/0/query"
    PAGE_SIZE = 1000  # Server maxRecordCount.
    # Every site page embeds window.allLockers (id -> detail link); the index is the stablest carrier.
    SLUG_URL = "https://www.pakettipiste.fi/noutopaikat/"

    async def start(self) -> AsyncIterator[Request]:
        yield Request(self.SLUG_URL, callback=self.parse_slugs, errback=self.err_slugs, dont_filter=True)

    def err_slugs(self, failure) -> Iterable[Request]:
        self.logger.warning(f"Slug page failed, continuing without websites: {failure.value}")
        self._inc("slug_page_error")
        yield self.make_api_request(0, {})

    def parse_slugs(self, response: Response) -> Iterable[Request]:
        slugs: dict[str, str] = {}
        blob = self.find_slug_blob(response.text)
        if not isinstance(blob, dict):
            self.logger.warning("Slug blob not found or not an object, continuing without websites")
            self._inc("unmapped/slug_blob")
        else:
            for key, entry in blob.items():
                link = entry.get("link") if isinstance(entry, dict) else None
                if isinstance(link, str) and (href := HREF_RE.search(link)):
                    slugs[str(key)] = response.urljoin(href.group(1))
                else:
                    self._inc("unmapped/slug_entry")
            self.logger.info(f"Parsed {len(slugs)} slug links")
            self._inc("slugs_parsed")
        yield self.make_api_request(0, slugs)

    def find_slug_blob(self, html: str) -> object:
        # Decode from the assignment start rather than regexing to ";": a non-greedy regex
        # would stop at a "};" inside a string value and lose every website.
        anchor = re.search(r"window\.allLockers\s*=\s*", html)
        if not anchor:
            return None
        try:
            blob, _ = json.JSONDecoder().raw_decode(html, anchor.end())
        except json.JSONDecodeError as e:
            self.logger.warning(f"Could not parse slug blob: {e}")
            return None
        return blob

    def make_api_request(self, offset: int, slugs: dict[str, str]) -> Request:
        params = {
            "where": "1=1",  # ArcGIS requires a where clause; 1=1 matches all rows.
            "outFields": "*",
            "returnGeometry": "true",
            "outSR": "4326",
            "orderByFields": "FID",  # Stable order so offset pages neither skip nor repeat rows.
            "resultOffset": offset,
            "resultRecordCount": self.PAGE_SIZE,
            "f": "json",
        }
        return Request(
            f"{self.API_URL}?{urlencode(params)}",
            callback=self.parse_features,
            errback=self.err_api,
            cb_kwargs={"offset": offset, "slugs": slugs},
            dont_filter=True,
        )

    def err_api(self, failure) -> None:
        # Scrapy's retry middleware runs first; this fires only once retries are exhausted.
        # Items already yielded are kept and any later page is lost, so a nonzero api_error
        # counter is the signal that a run was truncated rather than genuinely empty.
        offset = failure.request.cb_kwargs.get("offset")
        self.logger.error(f"Feature query failed at offset {offset}: {failure.value}")
        self._inc("api_error")

    def parse_features(self, response: Response, offset: int, slugs: dict[str, str]) -> Iterable[Request | Feature]:
        try:
            data = response.json()  # ty: ignore[unresolved-attribute]
        except json.JSONDecodeError:
            self._inc("api_bad_json")
            raise CloseSpider("pakettipiste_fi: feature query returned non-JSON") from None
        if not isinstance(data, dict):
            self._inc("api_bad_shape")
            raise CloseSpider("pakettipiste_fi: feature query returned non-object JSON")
        if data.get("error"):
            self._inc("api_error_response")
            raise CloseSpider(f"pakettipiste_fi: API error {data['error']}")
        features = data.get("features") or []
        if not features:
            if offset == 0:
                self._inc("empty_first_page")
                raise CloseSpider("pakettipiste_fi: no features on first page")
            self._inc("empty_page")
            self.logger.warning(f"No features at offset {offset}")
            return
        # Length fallback mirrors the shared ArcGIS finder; the flag alone is trusted otherwise.
        if data.get("exceededTransferLimit") or len(features) >= self.PAGE_SIZE:
            yield self.make_api_request(offset + len(features), slugs)
        for feature in features:
            item = self.parse_feature(feature, slugs)
            if item is not None:
                yield item

    def parse_feature(self, feature: dict, slugs: dict[str, str]) -> Feature | None:
        attrs = feature.get("attributes") or {}
        if attrs.get("Aktiivinen") != 1:
            self._inc(f"inactive/{attrs.get('Aktiivinen')}")
            return None
        if attrs.get("huolto_valmis_pvm") is not None:  # Listed separately as out of service.
            self._inc("maintenance")
            return None
        if attrs.get("ID") is None:
            self._inc("empty/ref")
            return None
        geometry = feature.get("geometry") or {}
        if geometry.get("x") is None or geometry.get("y") is None:
            self._inc("empty/coords")
            return None
        lokaatio = str(attrs.get("Lokaatio") or "").strip()
        kind = None
        if lokaatio.startswith(PICKUP_PREFIX):
            kind = PICKUP_PREFIX.strip()
            venue = lokaatio[len(PICKUP_PREFIX) :]
        else:
            venue = lokaatio
            for prefix in LOCKER_PREFIXES:
                if lokaatio.startswith(prefix):
                    kind = prefix.strip()
                    venue = lokaatio[len(prefix) :]
                    break
        venue = venue.strip()
        if kind is None or not venue:
            self._inc(f"unmapped/lokaatio/{lokaatio.replace('/', '-') or 'empty'}")
            return None
        sijoituspaikka = str(attrs.get("Sijoituspaikka") or "").strip()
        if sijoituspaikka != PLACEMENT_BY_KIND[kind]:
            self._inc(f"mismatch/sijoituspaikka/{kind}/{sijoituspaikka.replace('/', '-') or 'empty'}")
        is_pickup = kind == "Noutopiste"

        item = Feature()
        item["ref"] = str(attrs["ID"])
        item["lon"] = geometry["x"]
        item["lat"] = geometry["y"]
        item["country"] = "FI"
        for source, target in (
            ("Katuosoite", "street_address"),
            ("Postinumero", "postcode"),
            ("Postitoimipaikka", "city"),
        ):
            if value := str(attrs.get(source) or "").strip():
                if target == "postcode" and value.isdigit() and len(value) < 5:
                    value = value.zfill(5)  # Finnish postcodes are five digits; feed drops the leading zero.
                item[target] = value
            else:
                self._inc(f"empty/addr/{target}")
        item["opening_hours"] = self.parse_opening_hours(attrs)
        placement = str(attrs.get("Sijainti") or "").strip()
        if is_pickup:  # Manned counter run by the host shop.
            apply_category(Categories.GENERIC_POI, item)
            item["name"] = venue
            item["extras"]["post_office"] = "post_partner"
            item["extras"]["post_office:brand"] = BRAND
            apply_yes_no(Extras.PARCEL_PICKUP, item, True)
            if placement and placement != MANNED_LABEL:
                item["extras"]["description"] = placement
        else:  # Pakettipiste-operated locker; returns accepted at lockers.
            apply_category(Categories.PARCEL_LOCKER, item)
            item.update(OPERATOR)
            item["branch"] = venue
            apply_yes_no(Extras.PARCEL_PICKUP, item, True)
            apply_yes_no(Extras.PARCEL_MAIL_IN, item, True)
            if sijoituspaikka == PLACEMENT_BY_KIND[kind]:  # Agreed placement only; mismatch stays untagged.
                apply_yes_no("indoor", item, sijoituspaikka == "Sisällä", False)
            if placement:
                item["extras"]["description"] = placement
            else:
                self._inc("empty/placement")
        if website := slugs.get(str(attrs["ID"])):
            item["website"] = website
        else:
            self._inc("empty/website")
        return item

    def parse_opening_hours(self, attrs: dict) -> OpeningHours:
        oh = OpeningHours()
        for field in DAY_FIELDS:
            day = DAYS_FI[field]
            raw = attrs.get(field)
            if raw is None:  # Absence is not closure, so count it and skip the day.
                self._inc(f"empty/hours/{day}")
                continue
            if str(raw).strip() in ("", "-"):
                oh.set_closed(day)
                continue
            # Finnish dot-times and dash variants collapse to comma-separated HH:MM-HH:MM ranges.
            compact = re.sub(r"\s+", "", str(raw)).replace("–", "-").replace("—", "-").replace(".", ":")
            if compact in ("", "-"):
                oh.set_closed(day)
                continue
            if compact.casefold() == "24h":
                oh.add_range(day, "00:00", "24:00")
                continue
            ranges = self.day_ranges(compact)
            if ranges is None:
                continue
            for open_time, close_time in ranges:
                try:
                    oh.add_range(day, open_time, close_time)
                except ValueError:
                    self._inc("bad_range")
        return oh

    def day_ranges(self, compact: str) -> list[tuple[str, str]] | None:
        # A day may hold one range ("07:00-21:00") or a split shift ("09:00-12:00,13:00-17:00").
        ranges = []
        for part in re.split(r"[,;]", compact):
            match = RANGE_RE.fullmatch(part)
            if not match:
                self._inc(f"unmapped/hours/{compact.replace('/', '-')}")
                return None
            start = (int(match.group(1)), int(match.group(2)))
            end = (int(match.group(3)), int(match.group(4)))
            # add_range wraps absurd times onto other days instead of raising, so validate first.
            if start == end or not self.valid_time(*start) or not self.valid_time(*end, end_of_day=True):
                self._inc("bad_range")
                return None
            open_time = f"{start[0]:02d}:{start[1]:02d}"
            close_time = f"{end[0]:02d}:{end[1]:02d}"
            if open_time == "00:00" and close_time == "23:59":  # Only a midnight open implies 24h.
                close_time = "24:00"
            ranges.append((open_time, close_time))
        return ranges

    @staticmethod
    def valid_time(hour: int, minute: int, *, end_of_day: bool = False) -> bool:
        if not 0 <= minute <= 59:
            return False
        if hour == 24:
            return end_of_day and minute == 0  # 24:00 ends a day; it never starts one.
        return 0 <= hour <= 23

    def _inc(self, key: str) -> None:
        stats = getattr(getattr(self, "crawler", None), "stats", None)
        if stats is not None:
            stats.inc_value(f"atp/pakettipiste_fi/{key}")
