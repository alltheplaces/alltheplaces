import re

from scrapy import Spider

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature


class FriarTuxUSSpider(Spider):
    name = "friar_tux_us"
    item_attributes = {"brand": "Friar Tux"}
    start_urls = ["https://www.friartux.com/locations"]

    def parse(self, response):
        for link in response.xpath('//a[contains(@href, "/locations-") and contains(@href, ".html")]'):
            card = link.xpath('ancestor::*[.//a[starts-with(@href, "tel:")] and .//a[contains(@href, "daddr=")]][1]')
            if not card:
                continue

            address = card.xpath('normalize-space(.//a[contains(@href, "daddr=")][1])').get()
            address_parts = re.search(r",\s*([A-Z]{2})\s+(\d{5})$", address)
            if not address_parts:
                continue

            website = response.urljoin(link.attrib["href"])
            phone_href = card.xpath('.//a[starts-with(@href, "tel:")]/@href').get()
            item = Feature(
                ref=website.rsplit("/locations-", 1)[-1].removesuffix(".html"),
                addr_full=address,
                state=address_parts.group(1),
                postcode=address_parts.group(2),
                country="US",
                phone=phone_href.removeprefix("tel:") if phone_href else None,
                website=website,
            )

            hours = OpeningHours()
            for line in card.xpath(".//text()").getall():
                if closed_day := re.search(
                    r"closed\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)", line, re.I
                ):
                    hours.set_closed(closed_day.group(1))
                elif any(
                    day in line.lower()
                    for day in ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")
                ):
                    hours.add_ranges_from_string(line.strip())
            item["opening_hours"] = hours
            apply_category(Categories.SHOP_CLOTHES, item)
            yield item
