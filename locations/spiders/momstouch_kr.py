import re
from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import HtmlResponse

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature


class MomstouchKRSpider(Spider):
    name = "momstouch_kr"
    item_attributes = {"brand": "맘스터치", "brand_wikidata": "Q23044856"}
    start_urls = ["https://www.momstouch.co.kr/store/inner_shop_list.php?type=area"]
    requires_proxy = "KR"  # Direct requests from ATP CI timed out.
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response: HtmlResponse, **kwargs: Any) -> Iterable[Feature]:
        for store in response.xpath("//ul/li[dl]"):
            branch = store.xpath(".//dt/span/text()").get("").strip()
            if not branch:
                continue

            item = Feature(
                ref=branch,
                branch=branch,
                addr_full=store.xpath(".//div[dt/span]/dd/text()").get(),
                phone=store.xpath(".//div[dt[contains(., '전화번호')]]/dd/text()").get(),
            )

            onclick = store.xpath(".//dt/span/@onclick").get("")
            if match := re.search(r"set_shop_map\('([0-9.]+)',\s*'([0-9.]+)'\)", onclick):
                item["lat"], item["lon"] = map(float, match.groups())

            raw_hours = store.xpath(".//div[dt[contains(., '운영시간')]]/dd/text()").get("")
            if opening_hours := self.parse_opening_hours(raw_hours, branch):
                item["opening_hours"] = opening_hours

            apply_category(Categories.FAST_FOOD, item)
            yield item

    def parse_opening_hours(self, raw_hours: str, branch: str) -> OpeningHours | None:
        if not raw_hours.strip():
            return None

        match = re.search(r"(\d{1,2}:\d{2})~(\d{1,2}:\d{2})", raw_hours.replace(" ", ""))
        if not match:
            self.logger.debug("Unparsed opening hours for %s: %r", branch, raw_hours)
            return None

        opening_hours = OpeningHours()
        try:
            opening_hours.add_days_range(DAYS, *match.groups())
        except ValueError:
            self.logger.warning("Invalid opening hours for %s: %r", branch, raw_hours)
            return None

        return opening_hours or None
