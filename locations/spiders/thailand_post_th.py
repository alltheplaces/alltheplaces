import math
import re
from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature

API = "https://postbase-api.thailandpost.co.th/api/frontend/post_office/"
PAGE_SIZE = 1000


class ThailandPostTHSpider(Spider):
    name = "thailand_post_th"
    # Operator is set per item: Thailand Post Shops are franchises run by local businesses.
    allowed_domains = ["postbase-api.thailandpost.co.th"]
    # Service point finder: https://postbase.thailandpost.co.th/th/service-point

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield self.list_request(1)

    def list_request(self, page: int) -> JsonRequest:
        return JsonRequest(
            url=f"{API}list?lang=ENG&keyword=&page={page}&limit={PAGE_SIZE}&filter=", cb_kwargs={"page": page}
        )

    def parse(self, response: Response, page: int, **kwargs: Any) -> Any:
        result = response.json()["d"]
        if page == 1:
            for next_page in range(2, math.ceil(result["total"] / PAGE_SIZE) + 1):
                yield self.list_request(next_page)
        # The list has no coordinates, address or hours; those come from the detail endpoint.
        for office in result["data"]:
            yield JsonRequest(
                url=f"{API}detail?lang=ENG&slug={office['slug']}",
                callback=self.parse_office,
                cb_kwargs={"office": office},
            )

    def parse_office(self, response: Response, office: dict, **kwargs: Any) -> Any:
        details = response.json()["d"]["data"]
        if not details:
            return
        detail = details[0]
        item = Feature()
        item["ref"] = str(office["post_office_id"])
        # e.g. "ปณ.พระโขนง", "คปณ.พญาแล", "ปณร.พระโขนง 201 (อาคารมโนรม)": type abbreviation, then name
        item["branch"] = re.sub(r"^[\u0e00-\u0e7f]{1,4}\.\s*", "", office["title"].strip())
        item["lat"], item["lon"] = detail.get("latitude"), detail.get("longitude")
        item["addr_full"] = detail.get("address")
        item["postcode"] = office["postcode"]
        item["state"] = office["province_en"]
        item["city"] = office["district_en"]
        item["phone"] = detail.get("telephone")
        item["extras"]["post_office:type"] = office["post_category_code"]
        for hours in detail.get("office_hour") or []:
            if hours["service_category"] == "customer_service":
                item["opening_hours"] = self.parse_hours(hours)
        if office["post_category_code"] == "ปณร." or office["title"].startswith("ปณร."):
            # "ร้านไปรษณีย์ไทย" (Thailand Post Shop): a Thailand Post-branded franchise run by a local business
            apply_category(Categories.GENERIC_POI, item)
            item["extras"]["post_office"] = "post_partner"
            item["brand"], item["brand_wikidata"] = "ไปรษณีย์ไทย", "Q6676271"
        else:
            item["operator"], item["operator_wikidata"] = "Thailand Post", "Q6676271"
            apply_category(Categories.POST_OFFICE, item)
        yield item

    def parse_hours(self, hours: dict) -> OpeningHours | None:
        oh = OpeningHours()
        if not (hours.get("normal_day") or "").strip():
            return None
        for days, key in ((DAYS[:5], "normal_day"), (["Sa"], "saturday"), (["Su"], "sunday")):
            value = (hours.get(key) or "").strip()
            # e.g. "08:00 AM - 20:00 PM" (the AM/PM suffix is unreliable: 24-hour times are common)
            if match := re.fullmatch(r"(\d{1,2})[:.](\d{2})\s*([AP]M)?\s*-\s*(\d{1,2})[:.](\d{2})\s*([AP]M)?", value):
                start = self.to_24h(int(match[1]), match[2], match[3])
                end = self.to_24h(int(match[4]), match[5], match[6])
                if start < end:
                    oh.add_days_range(days, start, end)
                    continue
            elif value in ("", "-") or "ปิด" in value or "หยุด" in value:  # closed
                oh.set_closed(days)
                continue
            self.crawler.stats.inc_value(f"atp/{self.name}/hours/failed")
            return None
        return oh

    @staticmethod
    def to_24h(hour: int, minute: str, suffix: str | None) -> str:
        if suffix == "PM" and hour < 12:
            hour += 12
        elif suffix == "AM" and hour == 12:
            hour = 0
        return f"{hour:02d}:{minute}"
