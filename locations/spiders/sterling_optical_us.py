import re
from datetime import datetime
from typing import Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class SterlingOpticalUSSpider(Spider):
    name = "sterling_optical_us"
    item_attributes = {"brand": "Sterling Optical", "brand_wikidata": "Q7611451"}
    start_urls = ["https://www.sterlingoptical.com/locations/"]

    def parse(self, response: Response) -> Iterable[Feature]:
        for location in response.css("article.locationRow"):
            hours_rows = location.xpath(
                './/h4[normalize-space()="Location Hours"]/following-sibling::div[contains(@class, "row")]'
            )
            if not hours_rows:
                continue

            address_lines = [
                line.strip()
                for line in location.xpath('./div/address/span[contains(@class, "d-block")]/text()').getall()
                if line.strip()
            ]
            if not address_lines or not (
                locality := re.fullmatch(r"(.+),\s*([A-Z]{2})\s+(\d{5}(?:-\d{4})?)", address_lines[-1])
            ):
                continue

            city, state, postcode = locality.groups()
            title = location.css("h3 a::text").get("").strip()
            item = Feature(
                ref=location.attrib["id"].removeprefix("store-"),
                branch=title.rsplit(",", 1)[0],
                street_address=merge_address_lines(address_lines[:-1]),
                city=city,
                state=None if state == "VI" else state,
                postcode=postcode,
                country="VI" if state == "VI" else "US",
                phone=location.css("a.locationPhone::attr(href)").get("").removeprefix("tel:"),
                website=location.css("h3 a::attr(href)").get(),
            )

            hours = OpeningHours()
            for row in hours_rows:
                day = row.css("strong::text").get("").strip()
                hours_text = " ".join(row.css(".col-9::text").getall()).strip()
                if hours_text.lower() == "closed":
                    hours.set_closed(day)
                elif hours_match := re.fullmatch(r"(.+?[ap]m)\s*-\s*(.+?[ap]m)", hours_text, re.I):
                    start, end = hours_match.groups()
                    if datetime.strptime(start, "%I:%M%p") < datetime.strptime(end, "%I:%M%p"):
                        hours.add_range(day, start, end, time_format="%I:%M%p")
            item["opening_hours"] = hours

            apply_category(Categories.SHOP_OPTICIAN, item)
            yield item
