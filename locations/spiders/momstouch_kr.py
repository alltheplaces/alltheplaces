import re
from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature


class MomstouchKRSpider(Spider):
    name = "momstouch_kr"
    item_attributes = {"brand": "맘스터치", "brand_wikidata": "Q23044856"}
    start_urls = ["https://www.momstouch.co.kr/store/inner_shop_list.php?type=area"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        for store in response.xpath("//ul/li[dl]"):
            branch = store.xpath(".//dt/span/text()").get("").strip()
            if not branch:
                continue

            item = Feature()
            item["ref"] = item["branch"] = branch

            if onclick := store.xpath(".//dt/span/@onclick").get():
                if coord_match := re.search(r"set_shop_map\('([0-9.]+)',\s*'([0-9.]+)'\)", onclick):
                    item["lat"] = float(coord_match.group(1))
                    item["lon"] = float(coord_match.group(2))

            item["addr_full"] = store.xpath(".//div[dt/span]/dd/text()").get()
            item["phone"] = store.xpath(".//div[dt[contains(text(), '전화번호')]]/dd/text()").get()

            if raw_hours := store.xpath(".//div[dt[contains(text(), '운영시간')]]/dd/text()").get():
                if match := re.search(r"(\d{1,2}:\d{2})~(\d{1,2}:\d{2})", raw_hours.replace(" ", "")):
                    open_time, close_time = match.groups()
                    oh = OpeningHours()
                    oh.add_days_range(DAYS, open_time, close_time.replace("24:", "00:"), "%H:%M")
                    item["opening_hours"] = oh

            apply_category(Categories.FAST_FOOD, item)

            yield item
