import re
import unicodedata
from typing import Iterable

from scrapy import Spider
from scrapy.http import Request, Response

from locations.categories import Categories, Extras, PaymentMethods, apply_category, apply_yes_no
from locations.hours import OpeningHours
from locations.items import Feature

HOURS_RE = re.compile(r"(\d{1,2})[：:](\d{2})[～〜~](\d{1,2})[：:](\d{2})")
LATLNG_RE = re.compile(r"LatLng\('([\d.]+)',\s*'([\d.]+)'\)")
REGION_LINK_RE = re.compile(r"result\.php\?areaid=[a-z]+")


class WendysFirstKitchenJPSpider(Spider):
    name = "wendys_first_kitchen_jp"
    item_attributes = {
        "brand": "ウェンディーズ・ファーストキッチン",
        "brand_wikidata": "Q108525603",
        "extras": {
            "brand:en": "Wendy's First Kitchen",
            "brand:ja": "ウェンディーズ・ファーストキッチン",
        },
    }
    start_urls = ["https://wendys-firstkitchen.co.jp/shop/"]

    def parse(self, response: Response) -> Iterable[Request]:
        seen: set[str] = set()
        for href in response.xpath("//a[contains(@href, 'result.php?areaid=')]/@href").getall():
            if (link := REGION_LINK_RE.search(href)) and link.group(0) not in seen:
                seen.add(link.group(0))
                yield response.follow(link.group(0), callback=self.parse_region)

    def parse_region(self, response: Response) -> Iterable[Request]:
        for detail_url in response.xpath("//a[contains(@class, 'tomap')]/@href").getall():
            yield response.follow(detail_url, callback=self.parse_store)

    def parse_store(self, response: Response) -> Iterable[Feature]:
        item = Feature()
        item["name"] = "ウェンディーズ・ファーストキッチン"
        item["ref"] = response.url.split("shopid=", 1)[1]
        item["website"] = response.url

        if branch := response.xpath("//h4[@id='shopname']/text()").get():
            item["branch"] = branch.replace("【WFK】", "").strip()

        if address := response.xpath("//p[@id='address']/text()").get():
            item["addr_full"] = unicodedata.normalize("NFKC", address.strip())

        if phone := response.xpath("//ul[contains(@class, 'shop-info')]//li[contains(., 'TEL:')]/text()").get():
            phone = re.sub(r"TEL[:：]+", "", phone).strip()
            item["phone"] = f"+81 {phone}"

        if seats := response.xpath("//ul[contains(@class, 'shop-info')]/li[contains(., '席')]/text()").get():
            if m := re.search(r"(?:座席数|席数)\s*[:：]?\s*(.*?)(?:\n|$)", seats):
                clause = m.group(1)
                if "フード" not in clause and "ホテル" not in clause:
                    if split := re.search(r"禁煙(\d+)席\s*/\s*喫煙席?(\d+)席", clause):
                        item["extras"]["capacity:seats"] = str(int(split.group(1)) + int(split.group(2)))
                    elif first := re.search(r"(\d+)席", clause):
                        item["extras"]["capacity:seats"] = first.group(1)

        if latlng := LATLNG_RE.search(response.text):
            item["lat"], item["lon"] = latlng.groups()

        if (hours_text := response.xpath("string(//ul[contains(@class, 'biz-hours')]/li)").get()) and (
            m := HOURS_RE.search(hours_text)
        ):
            oh = OpeningHours()
            oh.add_days_range(
                ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"],
                f"{m.group(1)}:{m.group(2)}",
                f"{m.group(3)}:{m.group(4)}",
            )
            item["opening_hours"] = oh

        service_titles = response.xpath("//img[contains(@class, 're-icon')]/@title").getall()
        self._apply_services(item, service_titles)

        apply_category(Categories.FAST_FOOD, item)
        apply_yes_no(Extras.TAKEAWAY, item, True)

        yield item

    @staticmethod
    def _apply_services(item: Feature, titles: list[str]) -> None:
        # skipped flags (no valid OSM tag): マイカード (member loyalty card).
        apply_yes_no(Extras.WIFI, item, "WIFI" in titles, False)
        apply_yes_no("service:electricity", item, any(t.startswith("電源") for t in titles), False)
        has_card = any(t.startswith("クレジット") for t in titles)
        apply_yes_no(PaymentMethods.CREDIT_CARDS, item, has_card, False)
        apply_yes_no(PaymentMethods.ICSF, item, has_card, False)
        apply_yes_no("payment:qr_code", item, "QRコード決済" in titles, False)
        item["extras"]["smoking"] = "isolated" if "分煙" in titles else "no"
