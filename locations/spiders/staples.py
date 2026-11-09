from typing import Any, Iterable

from locations.items import Feature
from locations.storefinders.yext import YextSpider


class StaplesSpider(YextSpider):
    name = "staples"
    item_attributes = {"brand": "Staples", "brand_wikidata": "Q785943"}
    api_key = "a05b56686f7bf3558831122f8a32e69f"
    api_version = "20220927"

    def parse_item(self, item: Feature, location: dict, **kwargs: Any) -> Iterable[Feature]:
        # Only plain numeric refs are stores. "CP-…" and "TS-…" are services offered
        # at a store, "0" is the corporate HQ and "WO - …" is a Wayfair Outlet.
        if not item["ref"].isdigit() or item["ref"] == "0":
            return

        # The Yext websiteUrl points at a demo host; the real page is in a custom field.
        website = location.get("pgs_staplesPfmDemo_locationPages_f85io_Url")
        if website:
            item["website"] = website
        elif "pgsdemo.com" in (item.get("website") or ""):
            item["website"] = item["website"].replace("blithely-wrong-caiman.pgsdemo.com", "stores.staples.com")

        yield item
