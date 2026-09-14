import re
from typing import Iterable

from scrapy import Request, Spider

from locations.categories import apply_yes_no
from locations.google_url import extract_google_position
from locations.items import Feature

POSTCODE_RE = re.compile(r"〒(\d{3}-?\d{4})")
NAI_SUFFIX_RE = re.compile(r"[　\s]*内\s*$")

FORMAT_ICONS = {
    "3d": "cinema:3D",
    "4dx": "cinema:4DX",
    "imaxlaser": "cinema:IMAX",
}


class UnitedCinemasJPSpider(Spider):
    name = "united_cinemas_jp"
    item_attributes = {"brand": "ユナイテッド・シネマ", "brand_wikidata": "Q11345629"}
    start_urls = ["https://www.unitedcinemas.jp/index.html"]

    def parse(self, response) -> Iterable[Request]:
        for theater in response.xpath('//ul[@id="theaterList"]//li/a'):
            href = theater.xpath("@href").get()
            if not href or href.endswith("/"):
                continue
            slug = href.split("/")[1]
            detail_url = response.urljoin(f"/{slug}/about-theater.html")
            yield Request(
                url=detail_url,
                callback=self.parse_theater,
                meta={"slug": slug, "branch": theater.xpath("./img/@alt").get()},
            )

    def parse_theater(self, response) -> Iterable[Request]:
        slug = response.meta["slug"]
        addr_full = response.xpath('//p[@class="theaterAddress"]/text()').get()

        item = Feature()
        item["ref"] = slug
        item["branch"] = response.meta["branch"]
        item["website"] = response.urljoin(f"/{slug}/")

        if addr_full:
            if postcode_match := POSTCODE_RE.search(addr_full):
                item["postcode"] = postcode_match.group(1)
                addr_full = POSTCODE_RE.sub("", addr_full)
            item["addr_full"] = NAI_SUFFIX_RE.sub("", addr_full).strip()

        extract_google_position(item, response)

        facilities_url = response.urljoin(f"/{slug}/about_facilities.html")
        yield Request(url=facilities_url, callback=self.parse_facilities, meta={"item": item})

    def parse_facilities(self, response) -> Iterable[Feature]:
        item = response.meta["item"]

        screens = response.xpath('//td[contains(@class, "screen")]').getall()
        if screens:
            item["extras"]["screen"] = str(len(screens))

        for screen in screens:
            for icon, key in FORMAT_ICONS.items():
                if f"{icon}.gif" in screen:
                    apply_yes_no(key, item, True)

        yield item
