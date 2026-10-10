import math
import re
import unicodedata
from typing import AsyncIterator

import scrapy
from scrapy.http import Request

from locations.google_url import extract_google_position
from locations.hours import DAYS, OpeningHours
from locations.items import Feature


class GeoJPSpider(scrapy.Spider):
    name = "geo_jp"
    item_attributes = {"brand": "GEO", "brand_wikidata": "Q5533938"}
    allowed_domains = ["geo-online.co.jp"]

    async def start(self) -> AsyncIterator[Request]:
        for pref in range(1, 48):
            yield Request(
                f"https://geo-online.co.jp/store/search?type=pref&pref={pref:02d}",
                callback=self.parse_list,
                cb_kwargs={"pref": pref},
            )

    def parse_list(self, response, pref):
        for store in response.xpath('//div[contains(@class, "store_pref_unit")]'):
            href = store.xpath('.//a[contains(@href, "/store/")]/@href').get()
            if not href:
                continue
            yield Request(response.urljoin(href), callback=self.parse_store)

        total_text = response.xpath('//p[contains(@class, "pager_left")]/text()').get() or ""
        if m := re.search(r"全(\d+)件", total_text):
            total = int(m.group(1))
            pages = math.ceil(total / 20)
            for page in range(2, pages + 1):
                yield Request(
                    f"https://geo-online.co.jp/store/search?type=pref&pref={pref:02d}&p={page}",
                    callback=self.parse_list,
                    cb_kwargs={"pref": pref},
                )

    def parse_store(self, response):
        if not (table := response.xpath('//table[contains(@class, "store_detail_basic")]')):
            return

        fields = {}
        for tr in table.xpath(".//tr[th]"):
            label = "".join(tr.xpath("th//text()").getall()).replace(" ", "").replace("\u3000", "")
            value = " ".join(" ".join(tr.xpath("td//text()").getall()).split())
            fields[label] = value

        if not (name := response.xpath('//h1[contains(@class, "store_mainTitle")]/text()').get() or "").strip():
            return

        item = Feature()
        item["ref"] = re.search(r"/store/(\d+)/", response.url).group(1)
        item["branch"] = name.removeprefix("ゲオ")
        item["website"] = response.url

        extract_google_position(item, response)

        address = fields.get("住所", "")
        if m := re.match(r"〒\s*(\d{7})\s*(.*)", address):
            item["postcode"] = f"{m.group(1)[:3]}-{m.group(1)[3:]}"
            address = m.group(2)
        item["addr_full"] = unicodedata.normalize("NFKC", address)

        if phone := fields.get("電話"):
            item["phone"] = f"+81 {phone}"

        hours = fields.get("営業時間", "")
        self.add_hours(item, hours)

        if parking := re.search(r"(\d+)台", fields.get("駐車場", "")):
            item["extras"]["parking:capacity:standard"] = parking.group(1)

        yield item

    @staticmethod
    def add_hours(item, hours_text):
        oh = OpeningHours()
        main = hours_text.split("【")[0].strip()
        if "24時間" in main:
            oh.add_days_range(DAYS, "00:00", "23:59")
        elif m := re.search(r"(\d{1,2}:\d{2})〜(?:夜|深夜)?(\d{1,2}:\d{2})", main):
            oh.add_days_range(DAYS, m.group(1), m.group(2))
        else:
            return
        item["opening_hours"] = oh
