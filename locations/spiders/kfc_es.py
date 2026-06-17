from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature
from locations.spiders.kfc_us import KFC_SHARED_ATTRIBUTES


class KfcESSpider(Spider):
    """Spider for KFC restaurants in Spain.
    Closes #7706
    """

    name = "kfc_es"
    item_attributes = KFC_SHARED_ATTRIBUTES
    requires_proxy = True
    start_urls = ["https://api.kfc.es/find-a-kfc/allstores"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        for store in response.json():
            pa = store.get("primaryAttributes", {})
            gbd = store.get("googleBusinessData", {})
            loc = store.get("location", {})

            item = Feature()
            item["ref"] = pa.get("id")
            item["branch"] = pa.get("name", "").removeprefix("KFC ").strip() or None
            item["addr_full"] = gbd.get("address")
            item["phone"] = gbd.get("telephone") or None
            item["lat"] = loc.get("latitude")
            item["lon"] = loc.get("longitude")
            item["country"] = "ES"
            item["website"] = f"https://www.kfc.es/find-a-kfc/{pa.get('slug', '')}" if pa.get("slug") else None

            oh = OpeningHours()
            for day in DAYS_FULL:
                key = f"{day.lower()}Hours"
                if hours := gbd.get(key):
                    if hours.lower() != "closed":
                        try:
                            open_t, close_t = hours.split("-")
                            oh.add_range(day, open_t.strip(), close_t.strip())
                        except ValueError:
                            pass
                    else:
                        oh.set_closed(day)
            item["opening_hours"] = oh

            yield item
