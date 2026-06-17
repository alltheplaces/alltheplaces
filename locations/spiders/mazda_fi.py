import html
import json
import re
from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines
from locations.spiders.mazda_jp import MAZDA_SHARED_ATTRIBUTES


class MazdaFISpider(Spider):
    """Base spider for Mazda dealer finders using embedded JSON in a data-dealers attribute."""

    name = "mazda_fi"
    item_attributes = MAZDA_SHARED_ATTRIBUTES
    start_urls = ["https://www.mazda.fi/jalleenmyyjat"]
    country = "FI"

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        raw = response.xpath('//*[@id="find-dealer-app"]/@data-dealers').get()
        if not raw:
            return
        dealers = json.loads(html.unescape(raw))
        for dealer in dealers:
            services = dealer.get("dealerServices", [])
            base = {
                "branch": dealer["title"],
                "lat": dealer.get("latitude"),
                "lon": dealer.get("longitude"),
                "street_address": merge_address_lines([dealer.get("address1"), dealer.get("address2")]),
                "phone": self._clean_phone(dealer.get("phone")),
                "email": self._clean_email(dealer.get("email")),
                "website": (dealer.get("rightLink") or {}).get("url") or None,
                "country": self.country,
            }
            if not base["phone"]:
                base.pop("phone", None)
            if not base["email"]:
                base.pop("email", None)
            if not base["website"] or base["website"].startswith("mailto:"):
                base.pop("website", None)
            ref_base = str(dealer["id"])
            if "Sales" in services:
                item = Feature(**base)
                item["ref"] = ref_base + "_Sales"
                apply_category(Categories.SHOP_CAR, item)
                yield item
            if "Service" in services or "Parts" in services:
                item = Feature(**base)
                item["ref"] = ref_base + "_Service"
                apply_category(Categories.SHOP_CAR_REPAIR, item)
                yield item
            if not services:
                item = Feature(**base)
                item["ref"] = ref_base
                yield item

    def _clean_phone(self, value: str | None) -> str | None:
        if not value:
            return None
        # Some entries have multiple phone numbers separated by ; or newlines
        # Return just the first one
        first = re.split(r"[;\t\n]", value)[0].strip()
        # Strip any label prefix like "Automyynti puhelin: "
        first = re.sub(r"^[^:+0-9]*:", "", first).strip()
        return first or None

    def _clean_email(self, value: str | None) -> str | None:
        if not value:
            return None
        # Some entries have multiple emails - return just the first valid one
        m = re.search(r"[\w.+-]+@[\w.-]+\.\w+", value)
        return m.group(0) if m else None
