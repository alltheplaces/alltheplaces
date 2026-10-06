import re
from typing import Any

from scrapy import Request, Spider
from scrapy.http import Response
from scrapy.utils.httpobj import urlparse_cached

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature


class TheTacoStandUSSpider(Spider):
    name = "the_taco_stand_us"
    item_attributes = {"brand": "The Taco Stand"}
    start_urls = ["https://www.letstaco.com/locations"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for url in response.xpath('//a[.//p[normalize-space()="See Details"]]/@href').getall():
            yield Request(response.urljoin(url), callback=self.parse_location)

    def parse_location(self, response: Response) -> Feature:
        contact = response.css(".location-contact")
        address = contact.xpath('normalize-space(.//div[contains(@class, "flex-gap-1-1em")]/p)').get("")
        address_match = re.fullmatch(r"(.+),\s*([^,]+),\s*([A-Z]{2})\s+(\d{5})", address) or re.fullmatch(
            r"(.+?\b(?:St(?:reet)?|Rd|Road|Ave(?:nue)?|Hwy|Highway|Dr(?:ive)?|Blvd|Boulevard|Pkwy|Parkway|"
            r"Wy|Way|Cir(?:cle)?)\.?(?:\s+(?:(?:Suite|Ste|Unit|Space)\s+[#A-Za-z0-9.-]+|#[A-Za-z0-9.-]+))?)"
            r"\s*,?\s+"
            r"([^,]+),?\s+([A-Z]{2})\s+(\d{5})",
            address,
            re.I,
        )

        item = Feature(
            ref=urlparse_cached(response).path.rstrip("/").rsplit("/", 1)[-1],
            branch=contact.css("h2::text").get(),
            website=response.url,
            country="US",
        )

        phone_text = contact.xpath('normalize-space(.//div[contains(@class, "phone-flex")])').get("")
        if phone_match := re.search(r"\+?\d[\d\s()-]{7,}\d", phone_text):
            item["phone"] = phone_match.group(0)

        if address_match:
            item.update(
                {
                    "street_address": address_match.group(1),
                    "city": address_match.group(2),
                    "state": address_match.group(3),
                    "postcode": address_match.group(4),
                }
            )
        else:
            item["addr_full"] = address

        hours = OpeningHours()
        for row in response.css(".time-table-flex .table-unit"):
            day, time = row.css("p::text").getall()
            hours.add_ranges_from_string(f"{day.strip()} {time.strip()}")
        item["opening_hours"] = hours

        apply_category(Categories.FAST_FOOD, item)
        item["extras"]["cuisine"] = "mexican"
        return item
