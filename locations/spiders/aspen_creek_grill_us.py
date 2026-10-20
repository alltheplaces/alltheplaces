import re

import scrapy

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature


class AspenCreekGrillUSSpider(scrapy.Spider):
    name = "aspen_creek_grill_us"
    item_attributes = {"brand": "Aspen Creek Grill", "country": "US"}
    start_urls = ["https://aspencreekgrill.com/"]

    def parse(self, response):
        links = response.xpath(
            '//div[contains(@class, "et_pb_section")][.//h3[contains(., "Nearest Location")]]'
            '//a[contains(@class, "et_pb_button")]'
        )
        for link in links:
            yield response.follow(
                link.attrib["href"], self.parse_location, cb_kwargs={"branch": link.xpath("normalize-space(.)").get()}
            )

    def parse_location(self, response, branch):
        address = response.xpath(
            '//h4[normalize-space()="Address"]/following-sibling::div[1]//text()[normalize-space()]'
        ).getall()
        if len(address) != 2:
            self.logger.warning("Unexpected address at %s: %s", response.url, address)
            return

        street_address, locality = (part.strip() for part in address)
        match = re.fullmatch(r"([^,]+),\s*(Texas|TX|Indiana|IN|Kentucky|KY)\s*(\d{5})?", locality, re.I)
        if not match:
            self.logger.warning("Unexpected locality at %s: %s", response.url, locality)
            return

        state = {"texas": "TX", "indiana": "IN", "kentucky": "KY"}.get(match[2].lower(), match[2].upper())
        item = Feature(
            ref=response.url.rstrip("/").rsplit("/", 1)[-1],
            name=self.item_attributes["brand"],
            branch=branch,
            street_address=street_address,
            city=match[1].strip().title(),
            state=state,
            postcode=match[3],
            website=response.url,
        )

        hours = OpeningHours()
        for line in response.xpath(
            '//*[self::h4 or self::h6][normalize-space()="Hours"]/following-sibling::div[1]/p/text()'
        ).getall():
            if re.search(r"\d\s*(?:am|pm)", line, re.I):
                hours.add_ranges_from_string(line.replace(" & ", "-").replace(" – ", "-"))
        if hours.as_opening_hours():
            item["opening_hours"] = hours

        item["extras"]["cuisine"] = "american"
        apply_category(Categories.RESTAURANT, item)
        yield item
