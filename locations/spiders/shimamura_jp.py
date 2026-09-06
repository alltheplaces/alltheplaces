import re
from typing import Any

import scrapy
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.user_agents import FIREFOX_LATEST


class ShimamuraJPSpider(scrapy.Spider):
    name = "shimamura_jp"
    custom_settings = {
        # These browser headers were needed to avoid Akamai's HTTP 403 rejection
        "DEFAULT_REQUEST_HEADERS": {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "ja,en;q=0.9",
            "Connection": "keep-alive",
            "User-Agent": FIREFOX_LATEST,
        }
    }
    country_code = "JP"
    allowed_domains = ["www.shimamura.gr.jp"]

    # The /shop/list/ endpoint only emits per-store coordinates when a lat/lng pair is supplied
    TOKYO_LAT = "35.6762"
    TOKYO_LNG = "139.6503"
    LIST_URL = "https://www.shimamura.gr.jp/shop/list/?lat={lat}&lng={lng}&w="

    # brand sprite filename -> (brand, brand_wikidata)
    BRANDS = {
        "shimamura": ("しまむら", "Q7758173"),
        "avail": ("アベイル", "Q11284759"),
        "birthday": ("バースデイ", "Q11328509"),
        "chambre": ("シャンブル", "Q11307879"),
        "divalo": ("ディバロ", "Q130657060"),
    }

    async def start(self):
        yield scrapy.Request(
            self.LIST_URL.format(lat=self.TOKYO_LAT, lng=self.TOKYO_LNG),
            callback=self.parse_list,
        )

    def parse_list(self, response: Response, **kwargs: Any) -> Any:
        pager = response.css(".pager")
        if pager and self._current_step(response.url) == 0:
            last = max(int(s) for s in pager.re(r"step=(\d+)"))
            base = response.url.split("?", 1)[0]
            for step in range(1, last + 1):
                url = f"{base}?q=1&lat={self.TOKYO_LAT}&lng={self.TOKYO_LNG}&step={step}"
                yield scrapy.Request(url, callback=self.parse_list)

        for item in response.css("section.result-item"):
            item_url = item.css("a.result-item_link_url::attr(href)").get()
            if not item_url:
                continue
            ref = item_url.rsplit("_", 1)[1].removesuffix(".html")

            brand = self.BRANDS.get(self._brand_key(item), ("しまむら", "Q7758173"))

            poi = Feature()
            poi["extras"] = {}
            poi["ref"] = ref
            full_name = " ".join(item.css("h3.result-item_store *::text").getall()).strip()
            poi["name"] = brand[0]
            if branch := full_name.removeprefix(brand[0]).strip():
                poi["branch"] = branch
            poi["brand"] = brand[0]
            poi["brand_wikidata"] = brand[1]
            addr = " ".join(item.css(".result-item_address *::text").getall()).strip()
            parts = addr.split(None, 1)
            if len(parts) == 2:
                pref, rest = parts
                poi["addr_full"] = pref + rest
                poi["extras"]["addr:province"] = pref
            else:
                poi["addr_full"] = addr
            if phone := item.css(".result-item_tel a::text").get():
                poi["phone"] = phone.strip()

            poi["website"] = response.urljoin(item_url)
            coords = item.css(".zdc_distance")
            if coords:
                poi["lat"] = coords.attrib["lat"]
                poi["lon"] = coords.attrib["lng"]

            apply_category(Categories.SHOP_CLOTHES, poi)

            yield scrapy.Request(
                response.urljoin(item_url),
                callback=self.parse_detail,
                meta={"item": poi},
            )

    def parse_detail(self, response: Response, **kwargs: Any) -> Any:
        item = response.meta["item"]

        if zip_match := response.xpath("//dt[contains(text(),'所在地')]/following-sibling::dd[1]/text()").get():
            if m := re.search(r"〒\s*(\d{3}-\d{4})", zip_match):
                item["postcode"] = m.group(1)

        if hours_match := response.xpath("//dt[contains(text(),'営業時間')]/following-sibling::dd[1]/text()").get():
            if oh := self._parse_hours(hours_match.strip()):
                item["opening_hours"] = oh

        if coords := response.xpath("//script[contains(text(),'var lat =')]/text()").get():
            lat_match = re.search(r"var lat = ([\d.]+);", coords)
            lon_match = re.search(r"var lon = ([\d.]+);", coords)
            if lat_match and lon_match:
                item["lat"] = lat_match.group(1)
                item["lon"] = lon_match.group(1)

        yield item

    @staticmethod
    def _current_step(url: str) -> int:
        if "step=" in url:
            return int(url.split("step=", 1)[1].split("&", 1)[0])
        return 0

    @staticmethod
    def _brand_key(item) -> str | None:
        img = item.css(".result-item_store img::attr(src)").get() or ""
        if "sprite_circle_" in img:
            return img.split("sprite_circle_", 1)[1].split(".", 1)[0]
        return None

    @staticmethod
    def _parse_hours(text: str) -> OpeningHours | None:
        ranges = re.findall(r"(\d{1,2}):(\d{2})[〜～](\d{1,2}):(\d{2})", text)
        if not ranges:
            return None
        oh = OpeningHours()
        for h1, m1, h2, m2 in ranges:
            for day in DAYS:
                oh.add_range(day, f"{h1}:{m1}", f"{h2}:{m2}")
        return oh
