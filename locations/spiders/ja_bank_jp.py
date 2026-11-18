import re
import unicodedata
from typing import Any, AsyncIterator

import scrapy
from scrapy.http import Request, Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_WEEKDAY, OpeningHours
from locations.items import Feature


class JaBankJPSpider(scrapy.Spider):
    name = "ja_bank_jp"
    item_attributes = {
        "brand": "JAバンク",
        "brand_wikidata": "Q10854594",
        "extras": {"brand:en": "JA Bank", "brand:ja": "JAバンク"},
    }
    # job_role_id "1" = counter + ATM, "5" = counter only. "3" (ATM only) is
    # out of scope for this amenity=bank spider.
    JOB_ROLES = {"1": "yes", "5": "no"}

    async def start(self) -> AsyncIterator[Request]:
        yield Request("https://map.jabank.org/assets/data/list.json", callback=self.parse_prefectures)

    def parse_prefectures(self, response: Response, **kwargs: Any) -> Any:
        for pref in response.json()["data"]["prefecture"]:
            # mode=0 with an empty bank code returns every branch/ATM in the
            # prefecture in a single request, regardless of which of the many
            # (often 50-100+) local JA co-operatives operates it.
            yield scrapy.FormRequest(
                url="https://map.jabank.org/api/search_cond",
                formdata={"prefcode": pref["pref"], "mode": "0", "bank": ""},
                callback=self.parse_shops,
            )

    def parse_shops(self, response: Response, **kwargs: Any) -> Any:
        for shop in response.json()["data"]["shop_list"]:
            atm = self.JOB_ROLES.get(shop["job_role_id"])
            if atm is None:
                continue

            item = Feature()
            item["ref"] = shop["code"]
            item["name"] = shop["name"]
            item["operator"] = shop["official_name"]
            item["lat"] = shop["lat"]
            item["lon"] = shop["lng"]
            item["addr_full"] = shop["address"]
            item["postcode"] = shop["zip_code"]
            item["phone"] = shop["phone_number"]

            apply_category(Categories.BANK, item)
            item["extras"]["atm"] = atm

            yield scrapy.FormRequest(
                url="https://map.jabank.org/api/detail",
                formdata={"code": shop["code"], "type": "1"},
                callback=self.parse_details,
                cb_kwargs={"item": item},
            )

    def parse_details(self, response: Response, item: Feature, **kwargs: Any) -> Any:
        shop = response.json()["data"]
        oh = OpeningHours()
        for days, key in [
            (DAYS_WEEKDAY, "teller_window_business_hours"),
            (["Sa"], "teller_window_business_hours2"),
            (["Su"], "teller_window_business_hours3"),
        ]:
            text = unicodedata.normalize("NFKC", shop[key]).strip()
            if text == "定休日":
                oh.set_closed(days)
            elif match := re.fullmatch(r"(\d{1,2}:\d{2})\s*[~〜]\s*(\d{1,2}:\d{2})", text):
                oh.add_days_range(days, *match.groups())
        if oh.day_hours:
            item["opening_hours"] = oh
        yield item
