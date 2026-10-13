import re
from typing import Any, AsyncIterator

from scrapy import Request, Spider
from scrapy.http import Response

from locations.categories import Categories
from locations.hours import DAYS, DAYS_WEEKDAY, DAYS_WEEKEND, OpeningHours
from locations.items import Feature

# A few stores add a fallback mobile number after the store number, e.g.
# "048-950-1178（繋がらない場合は090-1910-3812までご連絡ください）".
PHONE_RE = re.compile(r"\d{2,5}-\d{1,4}-\d{3,4}")
TIME_RANGE_RE = re.compile(r"(\d{1,2}:\d{2})\s*[~～〜\-ー]\s*(\d{1,2}:\d{2})")

# Day labels used on the store pages, e.g. "【平日】", "土日祝", "【日曜祝日】" or "土曜：".
# Longer labels come first so "土日祝" is not read as "土".
DAY_LABELS = [
    ("平日・土日祝", DAYS),
    ("土日祝", DAYS_WEEKEND),
    ("平日", DAYS_WEEKDAY),
    ("土曜", ["Sa"]),
    ("日曜", ["Su"]),
]


class DaiwaCycleJPSpider(Spider):
    name = "daiwa_cycle_jp"
    item_attributes = {
        "brand": "ダイワサイクル",
        "brand_wikidata": "Q109598687",
        "extras": Categories.SHOP_BICYCLE.value,
    }
    allowed_domains = ["www.daiwa-cycle.co.jp"]

    async def start(self) -> AsyncIterator[Request]:
        # The map script on this page is broken, but the full store list is
        # rendered server side, with coordinates on each list item.
        yield Request("https://www.daiwa-cycle.co.jp/shop/default.aspx")

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.xpath('//section[@class="shop_list"]/ul/li'):
            item = Feature()
            item["website"] = response.urljoin(location.xpath('.//div[@class="btn01"]/a/@href').get())
            item["ref"] = item["website"].rstrip("/").rsplit("/", 1)[-1]
            item["name"], item["branch"] = self.parse_name(location.xpath(".//h2/text()").get())
            if item["name"] != self.item_attributes["brand"]:
                # Name tags from NSI would otherwise describe the main brand.
                item["extras"]["name:ja"] = item["name"]
                item["extras"]["name:en"] = item["name"].replace("ダイワサイクル", "Daiwa Cycle ")
            # One store has empty coordinate attributes. Its store page has no
            # coordinates either, so it is kept without a location.
            item["lat"] = location.xpath("@data-lat").get() or None
            item["lon"] = location.xpath("@data-lng").get() or None
            item["phone"] = self.parse_phone(
                location.xpath('.//dt[text()="TEL"]/following-sibling::dd[1]/text()').get()
            )
            # The store page adds the fax number and the hours for the stores
            # which leave them out of the list.
            yield Request(item["website"], callback=self.parse_store, cb_kwargs={"item": item})

    def parse_store(self, response: Response, item: Feature) -> Any:
        details = response.xpath('//div[@class="shop_detail"]/ul/li')

        def field(label: str) -> list[str]:
            return [
                text.strip()
                for text in details.xpath(f'.//b[text()="{label}"]/following-sibling::p[1]//text()').getall()
                if text.strip()
            ]

        if address := field("住所"):
            if address[0].startswith("〒"):
                item["postcode"] = address.pop(0).removeprefix("〒")
            item["addr_full"] = " ".join(address)
        if phone := self.parse_phone(" ".join(field("TEL"))):
            item["phone"] = phone
        if fax := self.parse_phone(" ".join(field("FAX"))):
            item["extras"]["fax"] = fax
        item["opening_hours"] = self.parse_hours(field("営業時間"))
        yield item

    @staticmethod
    def parse_phone(text: str | None) -> str | None:
        if text and (match := PHONE_RE.search(text)):
            return match.group(0)
        return None

    @staticmethod
    def parse_name(name: str) -> tuple[str, str]:
        # e.g. "ダイワサイクル 西宮鳴尾店", "ダイワサイクルSTYLE 東神奈川店",
        # "ダイワサイクルPRO 川崎野川店" or "ダイワサイクル芦屋店".
        match = re.match(r"(ダイワサイクル(?:STYLE|PRO)?)\s*(.+)", name.strip())
        return match.group(1), match.group(2)

    @staticmethod
    def parse_hours(lines: list[str]) -> OpeningHours | None:
        if any("時短" in line for line in lines):
            # A temporary reduced schedule is shown instead of the usual hours.
            return None
        oh = OpeningHours()
        parts = [part for line in lines for part in re.split(r"(?=【)", line)]
        for part in parts:
            # Full width digits and spaces are common, e.g. "10：00～20：00 （平　日）".
            part = re.sub(r"\s", "", part.translate(str.maketrans("０１２３４５６７８９：", "0123456789:")))
            if not (time_range := TIME_RANGE_RE.search(part)):
                continue
            for label, days in DAY_LABELS:
                if label in part:
                    break
            else:
                days = DAYS
            oh.add_days_range(days, *time_range.groups())
        return oh
