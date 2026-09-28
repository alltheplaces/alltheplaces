import re
from typing import Any, Iterable
from urllib.parse import parse_qs, urlparse

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_EN, OpeningHours
from locations.items import Feature


class ColtonsSteakHouseUSSpider(Spider):
    name = "coltons_steak_house_us"
    item_attributes = {"brand": "Colton's Steak House & Grill"}
    allowed_domains = ["www.coltonssteakhouse.com"]
    start_urls = ["https://www.coltonssteakhouse.com/map.php?loc=all"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Any]:
        yield from response.follow_all(
            response.xpath('//table[@id="maintable"]//a[contains(@href, "store_detail.php?id=")]/@href'),
            callback=self.parse_location,
        )

    def parse_location(self, response: Response) -> Iterable[Feature]:
        cells = response.xpath('//table[caption[contains(., "Restaurant Info")]]//tbody/tr/td')
        address_lines = [line.strip() for line in cells[0].xpath("./text()").getall() if line.strip()]
        if not address_lines or not (
            address_match := re.fullmatch(r"(.+),\s*([A-Z]{2})\s+(\d{5}(?:-\d{4})?)", address_lines[-1])
        ):
            return

        item = Feature(
            ref=parse_qs(urlparse(response.url).query)["id"][0],
            branch=(response.xpath("normalize-space(//h1)").get() or "")
            .replace("\N{NO-BREAK SPACE}", " ")
            .lstrip(": "),
            street_address=", ".join(address_lines[:-1]),
            city=address_match.group(1),
            state=address_match.group(2),
            postcode=address_match.group(3),
            country="US",
            phone=cells[1].xpath("normalize-space(string())").get(),
            website=response.url,
        )

        raw_hours = " ".join(line.strip() for line in cells[2].xpath("./text()").getall() if line.strip())
        raw_hours = re.sub(r"\bLunch\b.*$", "", raw_hours, flags=re.I)
        hours = OpeningHours()
        hours.add_ranges_from_string(raw_hours, days=DAYS_EN)
        item["opening_hours"] = hours

        apply_category(Categories.RESTAURANT, item)
        item["extras"]["cuisine"] = "steak_house"
        yield item
