import json
import re
from html import unescape
from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature


class ClaptonCraftGBSpider(Spider):
    """Spider for Clapton Craft bottle shops (London, UK).
    Closes #6999
    """

    name = "clapton_craft_gb"
    item_attributes = {"brand": "Clapton Craft", "brand_wikidata": "Q110154844"}
    start_urls = ["https://www.claptoncraft.co.uk/locations"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        # Each store is a Squarespace map block — location data is HTML-encoded JSON
        # in a data-* attribute on the block element.
        for m in re.finditer(r"data-[a-z-]+=[\"\'](\{&quot;.*?)[\"\'][\s>]", response.text):
            raw = unescape(m.group(1))
            try:
                d = json.loads(raw)
            except json.JSONDecodeError:
                continue

            loc = d.get("location", {})
            if not loc.get("markerLat"):
                continue

            item = Feature()
            item["ref"] = d.get("blockId")
            item["name"] = loc.get("addressTitle") or None
            item["street_address"] = loc.get("addressLine1") or None
            # addressLine2 contains city/postcode combined — leave as addr_full fallback
            addr2 = loc.get("addressLine2", "").strip()
            if addr2 and addr2.lower() not in ("united kingdom", ""):
                item["addr_full"] = ", ".join(filter(None, [loc.get("addressLine1"), addr2]))
            item["country"] = "GB"
            item["lat"] = loc["markerLat"]
            item["lon"] = loc["markerLng"]

            # Opening hours are in the single shared LD+JSON block
            oh_text = response.xpath(
                '//script[@type="application/ld+json"][contains(text(),"openingHours")]/text()'
            ).get()
            if oh_text:
                try:
                    ld = json.loads(oh_text)
                    if oh := ld.get("openingHours"):
                        item["opening_hours"] = OpeningHours()
                        item["opening_hours"].add_ranges_from_string(oh)
                except Exception:
                    pass

            apply_category(Categories.SHOP_ALCOHOL, item)
            yield item
