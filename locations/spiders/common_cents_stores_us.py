import json
import re
from typing import Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature

# The HubDB table backing this map mixes in rows that are not "Common Cents"
# convenience stores: a corporate office (no store_number), liquor stores
# licensed separately from the adjoining fuel store, and stand-alone
# restaurant concepts (Danielle Rivers) and duplicate/mis-geocoded car wash
# and Kwik Lube listings (Kraig Crawford) that repeat the address of a store
# already listed under a real store manager. Every row kept here carries
# both "convenience" and "gas" in its own includesfilters, confirming it's
# a genuine Common Cents c-store/fuel site.
EXCLUDED_MANAGERS = {None, "Danielle Rivers", "Kraig Crawford"}

# Several addresses run the street straight into the city with no space
# (e.g. "Jackson BlvdRapid City, SD 57702"), so a full street/city split
# isn't reliable across the dataset; only the trailing "ST ZIPCODE" is
# consistently well-formed, so that's all that gets pulled out structured.
STATE_ZIP_RE = re.compile(r"(?P<state>[A-Z]{2})\s+(?P<zip>\d{5})$")


class CommonCentsStoresUSSpider(Spider):
    name = "common_cents_stores_us"
    item_attributes = {"brand": "Common Cents"}
    start_urls = ["https://commoncentsstores.com/locations"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response: Response) -> Iterable[Feature]:
        # Store data is pre-rendered server-side into a JS array literal
        # (window.storeMapConfig.storeData) rather than served from an API.
        for values_json in re.findall(r"^\s*values: (\{.*\})\s*$", response.text, re.M):
            store = json.loads(values_json)

            if not store.get("store_number"):
                continue  # e.g. the corporate office, not a public store
            if store.get("manager") in EXCLUDED_MANAGERS:
                continue
            if "Liquor Store" in (store.get("hs_name") or ""):
                continue

            item = Feature()
            item["ref"] = str(store["store_number"])
            item["branch"] = store["hs_name"]
            item["lat"] = store.get("latitude")
            item["lon"] = store.get("longitude")
            item["phone"] = (store.get("phone") or "").strip() or None

            address = store.get("address") or ""
            item["addr_full"] = address
            if m := STATE_ZIP_RE.search(address):
                item["state"] = m.group("state")
                item["postcode"] = m.group("zip")

            # The "email" field is the regional manager's personal mailbox,
            # shared across every store they manage, not a branch contact.

            apply_category(Categories.SHOP_CONVENIENCE, item)
            apply_category(Categories.FUEL_STATION, item)

            yield item
