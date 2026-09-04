from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.storefinders.mapion import MapionSpider


class NttLePercJPSpider(MapionSpider):
    name = "ntt_le_perc_jp"
    item_attributes = {"brand": "NTTル・パルク", "brand_wikidata": "Q11236111"}
    allowed_domains = ["sasp.mapion.co.jp"]
    list_url = "https://sasp.mapion.co.jp/b/leperc/attr/?t=attr_con&start={}"

    def parse_item(self, item: Feature, data: dict, response: Response) -> Iterable[Feature]:
        item["ref"] = data.get("id")
        item["name"] = data.get("name")
        item["addr_full"] = data.get("full_address")
        item["country"] = "JP"
        item["lat"] = data.get("latitude")
        item["lon"] = data.get("longitude")

        if kencode := data.get("kencode"):
            item["state"] = f"JP-{kencode}"

        # tel is a single national maintenance hotline ("保守連絡先", i.e.
        # "maintenance contact") repeated identically across every location,
        # not a branch-specific number, so it is deliberately not extracted.

        # These are unattended coin-operated parking lots, so accessible
        # 24/7; the per-lot data only varies by-time-of-day pricing tier,
        # not by opening/closing hours.
        oh = OpeningHours()
        oh.add_days_range(DAYS, "00:00", "23:59")
        item["opening_hours"] = oh

        apply_category(Categories.PARKING, item)
        item["extras"]["fee"] = "yes"
        if car_count := data.get("car_count"):
            item["extras"]["capacity"] = car_count

        yield item
