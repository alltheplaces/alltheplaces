import re
from typing import Iterable

from scrapy.http import TextResponse
from unidecode import unidecode

from locations.categories import Categories, Clothes, apply_category, apply_clothes
from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines

LOCALES = {"FR": "fr_FR", "ES": "es_ES", "BE": "fr_BE", "PT": "pt_PT"}
# storeEvents is free text; a temporary closure needs both a "temporary" and a "closed" word (FR/ES/PT).
TEMPORARY = re.compile(r"\btemporai?r|\btemporal")
CLOSED = re.compile(r"\bferm|\bcerrad|\bcierr|\bfechad|\bencerrad")
CLOTHES = {
    "Retail men": [Clothes.MEN],
    "Retail men and women": [Clothes.MEN, Clothes.WOMEN],
    "Retail women": [Clothes.WOMEN],
}


class CelioSpider(JSONBlobSpider):
    name = "celio"
    item_attributes = {"brand": "Celio", "brand_wikidata": "Q2672003", "name": "Celio"}
    # Each locale only returns its own country's stores; no result cap observed at this radius.
    start_urls = [
        f"https://www.celio.com/on/demandware.store/Sites-celio-Site/{locale}/Stores-FindStores?lat=46.6&long=2.4&radius=20000"
        for locale in LOCALES.values()
    ]
    locations_key = "stores"
    # DataDome blocks plain requests, and Camoufox from CI IPs.
    requires_proxy = "FR"
    custom_settings = {
        # robots.txt disallows /on/demandware.store/.
        "ROBOTSTXT_OBEY": False,
        # Zyte gets a website ban with any custom User-Agent, so let it set its own.
        "ZYTE_API_SKIP_HEADERS": ["Cookie", "User-Agent"],
    }

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        events = unidecode(feature.get("storeEvents") or "").lower()
        if TEMPORARY.search(events) and CLOSED.search(events):
            self.logger.info(f"Skipping temporarily closed store {item.get('ref')}: {feature.get('storeEvents')}")
            return

        item["branch"] = (
            (item.pop("name", None) or "")
            .removeprefix("CELIO ")
            .removeprefix("MEN & WOMEN ")
            .removeprefix("WOMEN ")
            .removesuffix(" WOMEN")
        )
        item["street_address"] = merge_address_lines([feature.get("address1"), feature.get("address2")])
        # stateCode holds the country name.
        item.pop("state", None)
        if locale := LOCALES.get(feature.get("countryCode")):
            item["website"] = f"https://www.celio.com/{locale.lower().replace('_', '-')}/store?StoreID={item['ref']}"

        apply_category(Categories.SHOP_CLOTHES, item)
        if clothes := CLOTHES.get(feature.get("signboard")):
            apply_clothes(clothes, item)

        oh = OpeningHours()
        has_hours = False
        # storeSchedules starts on Monday.
        for day, hours in zip(DAYS, (feature.get("storeHours") or {}).get("storeSchedules") or []):
            morning = (hours or {}).get("morning") or {}
            afternoon = (hours or {}).get("afternoon") or {}
            am_open, am_close = morning.get("opening") or "", morning.get("closing") or ""
            pm_open, pm_close = afternoon.get("opening") or "", afternoon.get("closing") or ""
            if not (am_open or am_close or pm_open or pm_close):
                # The site shows empty days as closed.
                oh.set_closed(day)
                continue
            has_hours = True
            if am_close or pm_open:
                oh.add_range(day, am_open, am_close)
                oh.add_range(day, pm_open, pm_close)
            elif am_open and pm_close:
                # The site shows these days as a single opening-closing range.
                oh.add_range(day, am_open, pm_close)
        if has_hours:
            item["opening_hours"] = oh

        yield item
