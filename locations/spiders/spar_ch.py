import re
from typing import AsyncIterator, Iterable

from scrapy import Spider
from scrapy.http import Request, Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.spiders.spar_aspiag import SPAR_SHARED_ATTRIBUTES

# The store name indicates the store format, which maps to both a display
# name/category and (for "Supermarkt"/"mini"/"express") should not be kept
# as part of the branch name.
FORMATS = {
    "Supermarkt": ("Spar", Categories.SHOP_SUPERMARKET),
    "mini": ("Spar Mini", Categories.SHOP_CONVENIENCE),
    "express": ("Spar Express", Categories.SHOP_CONVENIENCE),
}


class SparCHSpider(Spider):
    name = "spar_ch"
    item_attributes = SPAR_SHARED_ATTRIBUTES
    allowed_domains = ["www.spar.ch"]
    # The store list also includes a small number of stores in Liechtenstein
    # (which shares Switzerland's postal system and is served from the same
    # .ch website), so let the country be determined per-item from
    # coordinates rather than assumed from the spider name or website domain.
    skip_auto_cc_spider_name = True
    skip_auto_cc_domain = True

    async def start(self) -> AsyncIterator[Request]:
        yield Request("https://www.spar.ch/sitemap.xml", callback=self.parse_sitemap_index)

    def parse_sitemap_index(self, response: Response) -> Iterable[Request]:
        for loc in response.xpath("//*[local-name()='loc']/text()").getall():
            if "sitemap=markets" in loc:
                yield Request(loc, callback=self.parse_sitemap)

    def parse_sitemap(self, response: Response) -> Iterable[Request]:
        for loc in response.xpath("//*[local-name()='loc']/text()").getall():
            yield Request(loc, callback=self.parse_store)

    def parse_store(self, response: Response) -> Iterable[Feature]:
        lat = response.xpath('//div[contains(@class,"js-map")]/@data-lat').get()
        lon = response.xpath('//div[contains(@class,"js-map")]/@data-lng').get()
        if not lat or not lon:
            return

        item = Feature()
        item["ref"] = response.url.rstrip("/").rsplit("/", 1)[-1]
        item["lat"] = lat
        item["lon"] = lon
        item["website"] = response.url

        title = re.sub(r"\s+", " ", response.xpath('//h1[@class="m-headline__title"]/text()').get("")).strip()
        raw = title.removeprefix("SPAR").strip()
        format_word, _, rest = raw.partition(" ")
        name, category = FORMATS.get(format_word, ("Spar", Categories.SHOP_SUPERMARKET))
        item["name"] = name
        item["branch"] = rest.strip() or raw
        apply_category(category, item)

        address_lines = [
            line.strip()
            for line in response.xpath('//address[contains(@class,"m-market-info__address")]/text()').getall()
            if line.strip()
        ]
        if len(address_lines) >= 1:
            item["street_address"] = address_lines[0]
        if len(address_lines) >= 2:
            if m := re.match(r"(\d{4})\s+(.*)", address_lines[1]):
                item["postcode"] = m.group(1)
                item["city"] = m.group(2).strip()
            else:
                item["addr_full"] = address_lines[1]
        if len(address_lines) >= 3:
            item["phone"] = address_lines[2]

        if email := response.xpath(
            '//address[contains(@class,"m-market-info__address")]//a[starts-with(@href,"mailto:")]/text()'
        ).get():
            item["email"] = email.strip()

        item["opening_hours"] = self.parse_hours(response)

        yield item

    @staticmethod
    def parse_hours(response: Response) -> OpeningHours:
        oh = OpeningHours()

        # Days are keyed by a numeric data attribute rather than the (occasionally
        # misspelt, e.g. "Mittvoch") German day-name label shown alongside it.
        for day_num, value_html in re.findall(
            r'data-item-week-day="(\d)">\s*<span class="m-market-info__list-item-key">[^<]*</span>'
            r'<span class="m-market-info__list-item-value">(.*?)</span>',
            response.text,
            re.S,
        ):
            day = DAYS[int(day_num) - 1]
            for part in re.split(r"<br\s*/?>", value_html):
                part = re.sub(r"<[^>]+>", "", part).strip()
                if not part or "durchgehend" in part.lower():
                    # "durchgehend geöffnet" ("continuously open") just confirms the
                    # single range above has no midday break; nothing further to add.
                    continue
                if "geschlossen" in part.lower():
                    oh.set_closed(day)
                    continue
                if m := re.search(r"(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})", part):
                    oh.add_range(day, m.group(1), m.group(2))

        return oh
