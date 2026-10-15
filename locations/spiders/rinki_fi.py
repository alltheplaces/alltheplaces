import re
from collections import Counter
from typing import Iterable

from scrapy import Spider
from scrapy.exceptions import CloseSpider
from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.settings import ITEM_PIPELINES


def _clean(value: object) -> str | None:
    # Feed strings are clean today; this guards edge whitespace and invisible chars.
    if not isinstance(value, str):
        return None
    return value.strip().strip("\u200b\u200c\ufeff").strip() or None


class RinkiFISpider(Spider):
    name = "rinki_fi"
    item_attributes = {"operator": "Suomen Pakkauskierrätys Rinki", "operator_wikidata": "Q11886224"}
    allowed_domains = ["rinkiin.fi"]
    start_urls = ["https://rinkiin.fi/wp-content/uploads/rinkiin-map/geo.json"]
    custom_settings = {
        "ITEM_PIPELINES": ITEM_PIPELINES | {"locations.pipelines.count_located_in.CountLocatedInPipeline": None}
    }

    # Fraction -> OSM tag; *_type ids are container hardware (same digits span fractions), presence means collected.
    MATERIAL_EXTRAS = {
        "carton": "recycling:cardboard",
        "glass": "recycling:glass_bottles",
        "metal": "recycling:cans",
        "plastic": "recycling:plastic_packaging",
        "paper": "recycling:paper",
        "clothing": "recycling:clothes",
        "eol_textiles": "recycling:textiles",
    }
    # Operational-only drops: team, contractors, collection/cleanup dates, municipality, vingo_id/id, text.

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._counts: Counter = Counter()

    def _count(self, key: str, n: int = 1) -> None:
        self._counts[key] += n
        crawler = getattr(self, "crawler", None)
        stats = crawler.stats if crawler else None
        if stats is not None:
            stats.inc_value(f"{self.name}/{key}", n)

    def parse(self, response: TextResponse) -> Iterable[Feature]:
        data = response.json()  # ty: ignore[unresolved-attribute]
        features = data.get("features", []) if isinstance(data, dict) else []
        if not features:
            raise CloseSpider("rinki_fi: empty feature list")
        items = [item for feature in features if (item := self.parse_feature(feature)) is not None]
        if not items:
            raise CloseSpider("rinki_fi: all features skipped")
        yield from items

    def parse_feature(self, feature: dict) -> Feature | None:
        if not isinstance(feature, dict):
            self._count("skipped/no_ref")
            self.logger.warning("Skipping non-dict feature")
            return None
        props = feature.get("properties")
        if not isinstance(props, dict):
            props = {}
        # ref is the public RINKI ID shown on point pages; vingo_id/id are internal keys.
        ref = _clean(props.get("rinki_id"))
        if not ref:
            self._count("skipped/no_ref")
            self.logger.warning("Skipping feature without rinki_id: %r", props.get("street"))
            return None
        if not re.match(r"^\d{2}-\d{5}$", ref):
            self._count("ref/unexpected_format")
            self.logger.warning("Unexpected rinki_id format: %r", ref)
        if props.get("text") is not None:
            self._count("unmapped/text")
        street = " / ".join(part for part in [_clean(props.get("street")), _clean(props.get("intersection"))] if part)
        if not street:
            self._count("empty/street")
        city = _clean(props.get("post_office"))
        if not city:
            self._count("empty/city")
        item = Feature(
            ref=ref, name="Rinki-ekopiste", street_address=street or None, city=city, geometry=feature.get("geometry")
        )
        if note := _clean(props.get("note")):
            item["located_in"] = note
        apply_category(Categories.RECYCLING, item)
        # Unstaffed outdoor container clusters, never staffed centres.
        item["extras"]["recycling_type"] = "container"
        for key, value in props.items():
            if not key.endswith("_type") or not value:
                continue
            fraction = key[: -len("_type")]
            if tag := self.MATERIAL_EXTRAS.get(fraction):
                item["extras"][tag] = "yes"
                self._count(f"material/{fraction}/yes")
            else:
                self._count(f"unmapped/{fraction}")
        for fraction in self.MATERIAL_EXTRAS:
            if not props.get(f"{fraction}_type"):
                self._count(f"material/{fraction}/no")
        # Fishing gear has no established recycling:* tag, hence absent from MATERIAL_EXTRAS.
        # Paper/clothing are partner-emptied but co-located point fractions, hence tagged.
        return item
