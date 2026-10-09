import re
from typing import Iterable

from scrapy import Request, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature


class UrbanEggUSSpider(Spider):
    name = "urban_egg_us"
    item_attributes = {"brand": "Urban Egg"}
    start_urls = ["https://www.urbanegg.com/locations/"]

    def parse(self, response: Response) -> Iterable[Request]:
        for link in response.xpath('//a[contains(@href, "/location/")]'):
            if "coming soon" in link.xpath("normalize-space(.)").get().lower():
                continue
            yield response.follow(link, callback=self.parse_location)

    def parse_location(self, response: Response) -> Iterable[Feature]:
        address = response.css(".et_pb_text_1_tb_body .et_pb_text_inner::text").getall()
        street, locality = [line.strip().strip(",") for line in address if line.strip()]
        city, state, postcode = re.fullmatch(r"(.+),\s*([A-Z]{2})\s+(\d{5})", locality).groups()
        website = response.css('link[rel="canonical"]::attr(href)').get() or response.url
        item = Feature(
            ref=website.rstrip("/").rsplit("/", 1)[-1],
            branch=response.css(".et_pb_text_0_tb_body h1::text").get(),
            street_address=street,
            city=city,
            state=state,
            postcode=postcode,
            country="US",
            phone=response.css(".et_pb_blurb_0_tb_body h3 span::text").get(),
            website=website,
        )
        hours = OpeningHours()
        item["branch"] = re.sub(r"\s*[-\u2013]\s*Now Open!?$", "", item["branch"], flags=re.I)
        for day in response.css(".weekdays"):
            line = " ".join(day.xpath("parent::*//text()").getall())
            hours.add_ranges_from_string(line)
        item["opening_hours"] = hours
        apply_category(Categories.RESTAURANT, item)
        yield item
