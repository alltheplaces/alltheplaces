import re
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_CN, DELIMITERS_EN, OpeningHours
from locations.items import Feature


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
        # e.g. "星期一至五,09:00 至 18:00;星期六,09:00 至 13:00" or "星期一至日,24小時"
        if not text:
            return None
        # "星期一至五" -> "星期一-星期五", so that both ends of the day range are full day names.
        text = re.sub(r"至([一二三四五六日])", r"-星期\1", text).replace("24小時", "00:00-24:00")
        oh = OpeningHours()
        oh.add_ranges_from_string(text, days=DAYS_CN, delimiters=DELIMITERS_EN + ["至"])
        return oh
