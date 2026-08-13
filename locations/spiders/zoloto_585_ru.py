from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.hours import DAYS_RU, NAMED_DAY_RANGES_RU, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class Zoloto585RUSpider(JSONBlobSpider):
    name = "zoloto_585_ru"
    item_attributes = {"brand_wikidata": "Q125730875"}
    start_urls = ["https://backend.zoloto585.ru/api/stores?blocked=0&active=1"]
    custom_settings = {"DOWNLOAD_TIMEOUT": 30, "ROBOTSTXT_OBEY": False}

    def pre_process_data(self, feature: dict) -> None:
        feature["ref"] = feature.pop("xmlId", None)
        feature.pop("name", None)
        feature["street_address"] = feature.pop("address", None)
        feature["addr_full"] = feature.pop("addressFull", None)
        feature["city"] = (feature.pop("city", None) or {}).get("name")
        feature.pop("phone", None)
        if email := feature.pop("email", None):
            feature["email"] = email.split(",")[0].strip()

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        if feature.get("isOnlyLombard"):
            self.crawler.stats.inc_value(f"atp/{self.name}/lombard_only_skipped")
            return
        if photos := feature.get("photos"):
            item["image"] = photos[0]

        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(
            feature.get("displaySchedule") or "", days=DAYS_RU, named_day_ranges=NAMED_DAY_RANGES_RU
        )

        apply_category(Categories.SHOP_JEWELRY, item)
        yield item
