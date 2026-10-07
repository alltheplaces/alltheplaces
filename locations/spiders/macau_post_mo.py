import re
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature

# Chinese weekday names used in "openingHours", e.g. "星期一至五,09:00 至 18:00;星期六,09:00 至 13:00".
DAYS_ZH = {"一": "Mo", "二": "Tu", "三": "We", "四": "Th", "五": "Fr", "六": "Sa", "日": "Su"}
DAY_ORDER = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]


class MacauPostMOSpider(Spider):
    name = "macau_post_mo"
    item_attributes = {"operator": "CTT", "operator_wikidata": "Q909429"}
    allowed_domains = ["www.ctt.gov.mo"]
    # Backing API of https://www.ctt.gov.mo/Contents/branches ("服務網點"); returns every postal counter.
    start_urls = ["https://www.ctt.gov.mo/apis/web/post-office/list?culture=zh-TW"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for office in response.json()["data"]["itemListElement"]:
            item = Feature()
            item["ref"] = office["branchCode"]
            item["name"] = office["legalName"]
            item["lat"] = office["latitude"]
            item["lon"] = office["longitude"]
            item["addr_full"] = " ".join(office["address"].split())
            item["phone"] = office.get("telephone")
            item["image"] = office.get("image")
            item["website"] = "https://www.ctt.gov.mo/Contents/branches"
            item["opening_hours"] = self.parse_hours(office.get("openingHours") or "")
            if office["branchCode"] in ("TETA", "HZMB"):
                # Self-service postal centres (自助郵務中心): 24/7 kiosks at ferry terminal / bridge checkpoint.
                item["extras"]["post_office:type"] = "self_service"
            if office["branchCode"] == "CMS":
                continue  # Communications Museum shop, not a postal counter
            apply_category(Categories.POST_OFFICE, item)
            yield item

    @staticmethod
    def parse_hours(text: str) -> OpeningHours | None:
        if not text:
            return None
        oh = OpeningHours()
        for part in text.split(";"):
            if "," not in part:
                continue
            days_text, times_text = part.split(",", 1)
            if "24小時" in times_text:
                times = [("00:00", "24:00")]
            else:
                times = re.findall(r"(\d{1,2}:\d{2})\s*至\s*(\d{1,2}:\d{2})", times_text)
            if m := re.search(r"星期([一二三四五六日])至([一二三四五六日])", days_text):
                start, end = DAY_ORDER.index(DAYS_ZH[m.group(1)]), DAY_ORDER.index(DAYS_ZH[m.group(2)])
                days = DAY_ORDER[start : end + 1]
            elif m := re.search(r"星期([一二三四五六日])", days_text):
                days = [DAYS_ZH[m.group(1)]]
            else:
                continue
            for day in days:
                for open_time, close_time in times:
                    oh.add_range(day, open_time, close_time)
        return oh
