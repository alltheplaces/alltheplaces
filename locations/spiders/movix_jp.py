from collections.abc import AsyncIterator
from typing import Iterable

from scrapy import Request, Spider

from locations.google_url import extract_google_position
from locations.items import Feature

THEATER_LIST_URL = "https://www.smt-cinema.com/assets/module/page_theater_list_partner.html"


class MovixJPSpider(Spider):
    name = "movix_jp"
    item_attributes = {"brand": "MOVIX", "brand_wikidata": "Q11532184"}

    async def start(self) -> AsyncIterator[Request]:
        yield Request(url=THEATER_LIST_URL, callback=self.parse_theater_list)

    def parse_theater_list(self, response) -> Iterable[Request]:
        for href in response.xpath("//a[contains(@href, '/site/')]/@href").getall():
            yield Request(
                url=response.urljoin(href.rstrip("/") + "/access.html"),
                callback=self.parse_theater,
            )

    def parse_theater(self, response) -> Iterable[Feature]:
        item = Feature()
        item["ref"] = response.url.split("/site/")[1].split("/")[0]

        extract_google_position(item, response)

        name = response.xpath('//meta[@property="og:site_name"]/@content').get("").split(" | ")[0].strip()
        item["name"], item["branch"] = self.name_branch_for(name)
        if address := self.extract_address(response):
            item["addr_full"] = address

        if phone := response.xpath(
            '//div[contains(@class, "phone")]//a[starts-with(@href, "tel:")]/span/text()[1]'
        ).get():
            item["phone"] = f"+81 {phone.strip()}"

        yield item

    @staticmethod
    def extract_address(response) -> str | None:
        parts = response.xpath(
            '//h3[contains(text(), "所在地")]/following-sibling::p[not(a)]/text()'
            ' | //h3[contains(text(), "所在地")]/following-sibling::p[not(a)]/span/text()'
        ).getall()
        for part in parts:
            part = part.strip()
            if part and not part.startswith(("【", "（", "▶")):
                return part
        return None

    @staticmethod
    def name_branch_for(name: str) -> tuple[str | None, str | None]:
        if name.startswith("MOVIX"):
            return None, name[5:] or None
        return name, None
