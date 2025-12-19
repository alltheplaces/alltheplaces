from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class ValoraSpider(JSONBlobSpider):
    name = "valora"
    start_urls = ["https://bazaar.valoraapis.com/public/stores"]
    brands = {
        # For most Valora brands, we take tags such as "shop=bakery"
        # from the OpenStreetMap Name Suggestion Index (NSI).
        "avec": ("avec", "Q103863974", Categories.SHOP_CONVENIENCE),
        "backfactory": ("Back-Factory", "Q21200483", Categories.SHOP_BAKERY),
        "backwerk": ("BackWerk", "Q798298", Categories.SHOP_BAKERY),
        "bki": ("Brezelkönig", "Q111728604", Categories.FAST_FOOD),
        "brezelkoenig": ("Brezelkönig", "Q111728604", Categories.FAST_FOOD),
        "CIGO": ("Cigo", "Q113290782", Categories.SHOP_NEWSAGENT),
        "ditsch": ("Ditsch", "Q911573", Categories.SHOP_BAKERY),
        "Service Store DB": ("ServiceStore DB", "Q84482517", Categories.SHOP_KIOSK),
        "Service Store DB + P&B": ("ServiceStore DB", "Q84482517", Categories.SHOP_KIOSK),
        "spettacolo": ("Caffè Spettacolo", "Q111728781", Categories.CAFE),
        "superguud": ("Superguud", "", Categories.FAST_FOOD),
        "U-Store": ("U-Store", "Q113290511", Categories.SHOP_CONVENIENCE),
        # However, the AllThePlaces pipeline does not apply any NSI rules
        # if multiple rules match with conflicting tags. We have asked the
        # local mapping community if and how exactly the conflicting NSI rules
        # should be cleaned up for "k kiosk" and "Press & Books". Meanwhile,
        # we make a call for AllThePlaces.
        "kkiosk": ("k kiosk", "Q60381703", Categories.SHOP_NEWSAGENT),
        "pressAndBooks": ("Press & Books", "Q100407277", Categories.SHOP_BOOKS),
        # In real life, the stores formerly called “K presse + books” have been
        # re-branded as “Press & Books”. But, the Valora JSON feed still uses the old name.
        "K presse + books": ("Press & Books", "Q100407277", Categories.SHOP_BOOKS),
    }

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["street_address"] = item.pop("street", None)
        if not item["street_address"]:
            return
        item["brand"], item["brand_wikidata"], category = self.brands.get(feature["format"], (None, None, None))
        if category:
            apply_category(category, item)

        item["opening_hours"] = OpeningHours()
        for day, hours in feature.get("openingHours").items():
            for shift in hours:
                item["opening_hours"].add_range(day, shift.get("from"), shift.get("to"))
        yield item
