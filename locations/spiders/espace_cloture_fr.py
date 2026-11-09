import re
from html import unescape
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_FR, OpeningHours, day_range, sanitise_day
from locations.items import Feature


class EspaceClotureFRSpider(Spider):
    name = "espace_cloture_fr"
    item_attributes = {"name": "Espace Clôture", "brand": "Espace Clôture", "brand_wikidata": "Q126880049"}
    start_urls = ["https://www.espace-cloture.fr/agence/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        markers = {
            unescape(marker.xpath("@data-title").get()): marker.xpath("@data-lat|@data-lng").getall()
            for marker in response.xpath('//div[contains(@class, "js-marker")]')
        }
        for card in response.xpath('//article[@class="agency-archive-card"]'):
            title = card.xpath("h3/text()").get()
            item = Feature()
            name, item["branch"] = re.split(r" [–-] ", title, maxsplit=1)
            if name != "ESPACE CLÔTURE":
                item["name"] = name
            item["lat"], item["lon"] = markers.get(title, (None, None))
            item["addr_full"] = card.xpath('normalize-space(.//a[contains(@class, "metas-text")])').get()
            if m := re.search(r"^(.+?),? (\d{5}) (.+)$", item["addr_full"]):
                item["street_address"], item["postcode"], item["city"] = m.groups()
            item["phone"] = card.xpath('.//a[starts-with(@href, "tel:")]/@href').get("").removeprefix("tel:")
            item["opening_hours"] = self.parse_hours(
                card.xpath('.//li[contains(@class, "metas-text")]/text()').getall()
            )
            apply_category(Categories.SHOP_TRADE, item)
            apply_category(Categories.TRADE_FENCING, item)
            link = card.xpath('.//a[contains(@class, "links-right-link")]/@href').get()
            item["ref"] = link.rsplit("p=", 1)[1]
            yield response.follow(
                link,
                callback=self.parse_website,
                cb_kwargs={"item": item},
            )

    def parse_website(self, response: Response, item: Feature) -> Any:
        item["website"] = response.url
        yield item

    @staticmethod
    def parse_hours(lines: list[str]) -> OpeningHours | None:
        oh = OpeningHours()
        days = []
        has_times = False
        for line in map(str.strip, lines):
            if line.lower().startswith("fermé"):
                for word in line.split():
                    if day := sanitise_day(word, DAYS_FR):
                        oh.set_closed(day)
            elif m := re.fullmatch(r"(?:du |le )?(\w+)(?: au (\w+))?", line, re.IGNORECASE):
                start, end = sanitise_day(m[1], DAYS_FR), sanitise_day(m[2] or m[1], DAYS_FR)
                days = day_range(start, end) if start and end else []
            else:
                for h1, m1, h2, m2 in re.findall(r"(\d{1,2})[:h](\d{2})?\s*[–-]\s*(\d{1,2})[:h](\d{2})?", line):
                    oh.add_days_range(days, f"{h1}:{m1 or '00'}", f"{h2}:{m2 or '00'}")
                    has_times = True
        return oh if has_times else None
