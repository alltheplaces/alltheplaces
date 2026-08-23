import re
from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import Request, Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature

POSTCODE_RE = re.compile(r"〒(\d{3}-\d{4})\s*")
HOURS_RE = re.compile(r"(\d{1,2}:\d{2})\s*[~〜～-]\s*(\d{1,2}:\d{2})")
COORD_RE = re.compile(r"!2d(-?[\d.]+)!3d(-?[\d.]+)")


class AdoresJPSpider(Spider):
    name = "adores_jp"
    item_attributes = {"brand": "アドアーズ", "brand_wikidata": "Q54843532"}
    allowed_domains = ["www.adores.jp"]
    start_urls = ["https://www.adores.jp/tenpo/"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Request]:
        for block in response.css("div.storeblock"):
            # A handful of stores are marked as permanently closed but the
            # <div> is left in the page (rather than removed or commented out).
            if block.css("div.storelink.closed"):
                continue

            href = block.css('div.storeinfo a[href$=".html"]::attr(href)').get()
            if not href:
                continue

            name = block.css("div.storeinfo h3::text").get("").strip()
            texts = block.css("div.storeinfo p::text").getall()
            if len(texts) < 3:
                # Some closed stores are left in the page with a single
                # closure notice paragraph instead of address/tel/hours
                # (e.g. "閉店致しました（2026/1/18）"), rather than being
                # removed or marked with the "closed" class used elsewhere.
                continue
            address_raw = texts[0].strip()
            phone = texts[1].removeprefix("TEL:").strip()
            hours_raw = texts[2].removeprefix("営業時間:").strip()

            yield response.follow(
                href,
                callback=self.parse_store,
                cb_kwargs={
                    "name": name,
                    "address_raw": address_raw,
                    "phone": phone,
                    "hours_raw": hours_raw,
                },
            )

    def parse_store(
        self, response: Response, name: str, address_raw: str, phone: str, hours_raw: str
    ) -> Iterable[Feature]:
        ref_match = re.search(r"/([^/]+)\.html$", response.url)
        if not ref_match:
            return
        ref = ref_match.group(1)

        item = Feature()
        item["ref"] = ref
        item["branch"] = name.removeprefix("アドアーズプラス").removeprefix("アドアーズ").strip()
        item["country"] = "JP"
        item["phone"] = phone or None
        item["website"] = response.url

        postcode_match = POSTCODE_RE.search(address_raw)
        if postcode_match:
            item["postcode"] = postcode_match.group(1)
            item["addr_full"] = POSTCODE_RE.sub("", address_raw).strip()
        else:
            item["addr_full"] = address_raw

        iframe_src = response.css("td.listmapr-real iframe::attr(src)").get()
        if iframe_src and (coord_match := COORD_RE.search(iframe_src)):
            item["lon"], item["lat"] = coord_match.groups()

        if hours_raw and (hours_match := HOURS_RE.search(hours_raw)):
            oh = OpeningHours()
            oh.add_days_range(DAYS, hours_match.group(1), hours_match.group(2))
            item["opening_hours"] = oh

        apply_category(Categories.LEISURE_AMUSEMENT_ARCADE, item)

        yield item
