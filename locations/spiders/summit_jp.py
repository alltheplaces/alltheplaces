import re
from typing import AsyncIterator, Iterable, Optional

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature

# Coordinates for each store are not available from the store list/detail
# JSON APIs directly. They are embedded in the "pb" parameter of a Google
# Maps embed URL returned in the "map" field, e.g.:
#   ...!1d3237.3!2d139.80889!3d35.76736400000001!2m3!1f0!2f0!3f0...
# where "2d" is the longitude and "3d" is the latitude of the map centre
# (which corresponds to the store's marker location).
MAP_COORDS_RE = re.compile(r"!2d(?P<lon>[\d.\-]+)!3d(?P<lat>[\d.\-]+)")

POSTCODE_ADDRESS_RE = re.compile(r"〒(?P<postcode>\d{3}-\d{4})\s*(?P<addr_full>.+)")

# area "label" looks like "東京都足立区" (prefecture + city/ward); pull just
# the prefecture (ending in 都/道/府/県) off the front for item["state"].
PREFECTURE_RE = re.compile(r"^(?P<state>.+?[都道府県])")

HOURS_RE = re.compile(r"(?P<open>\d{1,2}:\d{2})\s*[~～]\s*(?P<close>\d{1,2}:\d{2})")


class SummitJPSpider(Spider):
    name = "summit_jp"
    item_attributes = {"brand": "サミット", "brand_wikidata": "Q11305129"}
    LIST_URL = "https://mng.content-smt-site.net/wp-json/custom/v1/store"
    DETAIL_URL = "https://mng.content-smt-site.net/wp-json/custom/v1/store/{}"

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(url=self.LIST_URL, callback=self.parse_list)

    def parse_list(self, response: Response) -> Iterable[JsonRequest]:
        for store in response.json():
            if not any(t.get("value") == "summit" for t in store.get("type", [])):
                # Some locations only host a co-located "Colmopia" drugstore
                # tenant with no Summit supermarket on site; skip those.
                continue

            slug = store["slug"]
            area = store.get("area", {})
            area_value = area.get("value", "")
            # area "value" looks like "01000_tokyo_adachi"; the store detail
            # page URL uses the prefecture romaji segment, e.g. "tokyo".
            prefecture = area_value.split("_")[1] if area_value.count("_") >= 1 else ""

            state = None
            if m := PREFECTURE_RE.match(area.get("label", "")):
                state = m.group("state")

            yield JsonRequest(
                url=self.DETAIL_URL.format(slug),
                callback=self.parse_store,
                cb_kwargs={"slug": slug, "prefecture": prefecture, "state": state},
            )

    def parse_store(self, response: Response, slug: str, prefecture: str, state: Optional[str]) -> Iterable[Feature]:
        store = response.json()

        item = Feature()
        item["ref"] = slug
        item["name"] = self.item_attributes["brand"]
        item["branch"] = store.get("title")
        item["website"] = f"https://www.summitstore.co.jp/store/{prefecture}/post/?id={slug}"
        item["country"] = "JP"
        item["state"] = state

        if address := store.get("address"):
            if m := POSTCODE_ADDRESS_RE.match(address):
                item["postcode"] = m.group("postcode")
                item["addr_full"] = m.group("addr_full")
            else:
                item["addr_full"] = address

        if phone := self.extract_summit_field(store.get("tel")):
            item["phone"] = f"+81 {phone}"

        if fax := store.get("fax"):
            item["extras"]["fax"] = f"+81 {fax}"

        if map_url := store.get("map"):
            if m := MAP_COORDS_RE.search(map_url):
                item["lat"] = m.group("lat")
                item["lon"] = m.group("lon")

        if hours := self.extract_summit_field(store.get("hours")):
            if opening_hours := self.parse_hours(hours):
                item["opening_hours"] = opening_hours

        apply_category(Categories.SHOP_SUPERMARKET, item)

        yield item

    @staticmethod
    def extract_summit_field(raw: Optional[str]) -> Optional[str]:
        """Fields such as "hours" and "tel" sometimes bundle information for
        a co-located "Colmopia" drugstore tenant, separated by line breaks
        and prefixed with a Japanese brand label, e.g.:
            "サミット：9:00～1:00\r\nコルモピア：10:00～20:00"
        Extract just the "サミット" (Summit) portion where present, falling
        back to the raw value when it isn't split by brand at all."""
        if not raw:
            return None
        lines = [line.strip() for line in raw.splitlines() if line.strip()]
        if not lines:
            return None
        for line in lines:
            if m := re.match(r"^サミット[：:]\s*(.+)$", line):
                return m.group(1).strip()
        return lines[0]

    @staticmethod
    def parse_hours(hours: str) -> Optional[OpeningHours]:
        if not (m := HOURS_RE.match(hours)):
            return None

        oh = OpeningHours()
        for day in DAYS:
            oh.add_range(day, m.group("open"), m.group("close"))

        return oh
