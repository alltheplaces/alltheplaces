import re
from typing import Iterable

from scrapy import Request, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_CZ, OpeningHours
from locations.items import Feature

LAT_LON_PATTERN = re.compile(r'new google\.maps\.LatLng\("(-?[\d.]+)",\s*"(-?[\d.]+)"\)')
# The site sometimes inserts invisible characters (word joiners, zero-width
# spaces, etc.) around the hyphen/en-dash separating opening/closing times,
# which breaks opening hours parsing if left in place.
INVISIBLE_CHARS_PATTERN = re.compile("[\u200b\u200c\u200d\u2060\ufeff]")


class ReznictviRabbitCZSpider(Spider):
    name = "reznictvi_rabbit_cz"
    item_attributes = {"brand": "Řeznictví RABBIT", "brand_wikidata": "Q140309856"}
    allowed_domains = ["www.reznictvirabbit.cz"]
    start_urls = ["https://www.reznictvirabbit.cz/vase-reznictvi/"]

    def parse(self, response: Response) -> Iterable[Request]:
        for url in response.xpath('//div[@class="list row"]//li/a/@href').getall():
            yield Request(response.urljoin(url), callback=self.parse_store)

    def parse_store(self, response: Response) -> Iterable[Feature]:
        item = Feature()
        item["ref"] = item["website"] = response.url
        item["country"] = "CZ"
        item["name"] = self.item_attributes["brand"]

        item["branch"] = response.xpath('//li[@class="last"]/text()').get("").strip()

        address_lines = [
            line.strip()
            for line in response.xpath(
                '//h2[contains(., "Adresa")]/following-sibling::div[@class="text"][1]//text()'
            ).getall()
            if line.strip()
        ]
        if len(address_lines) >= 2:
            item["street_address"] = address_lines[0]
            city_postcode = address_lines[1]
            if "," in city_postcode:
                city, postcode = city_postcode.rsplit(",", 1)
                item["city"] = city.strip()
                postcode = postcode.strip().replace(" ", "")
                if len(postcode) == 5 and postcode.isdigit():
                    postcode = postcode[:3] + " " + postcode[3:]
                item["postcode"] = postcode
            else:
                item["city"] = city_postcode

        item["phone"] = (
            response.xpath(
                '//strong[contains(text(), "Telefon")]/ancestor::div[@class="text"][1]//a[starts-with(@href, "tel:")]/@href'
            )
            .get("")
            .removeprefix("tel:")
        )

        if m := LAT_LON_PATTERN.search(response.text):
            item["lat"], item["lon"] = m.groups()

        oh = OpeningHours()
        for row in response.xpath('//h2[contains(., "Otevírací doba")]/following-sibling::div[@class="text"][1]//tr'):
            day = row.xpath("./td[1]/text()").get()
            hours = row.xpath("normalize-space(./td[2])").get()
            if not day or not hours:
                continue
            hours = INVISIBLE_CHARS_PATTERN.sub("", hours).strip()
            if "|" in hours:
                # A handful of stores share a table with an attached bistro,
                # e.g. "Řeznictví 7:30-17:00 | Bistro 7:30-15:00"; keep only
                # the butcher shop's hours.
                parts = [p.strip() for p in hours.split("|")]
                hours = next((p for p in parts if "řeznictví" in p.lower()), parts[0])
                hours = re.sub(r"(?i)^řeznictví\s*", "", hours).strip()
            if not hours or "zavřeno" in hours.lower() or "připravujeme" in hours.lower():
                continue
            oh.add_ranges_from_string(f"{day.strip()} {hours}", days=DAYS_CZ)
        item["opening_hours"] = oh

        apply_category(Categories.SHOP_BUTCHER, item)

        yield item
