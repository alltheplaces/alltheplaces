import re
from html import unescape
from typing import Iterable

from scrapy import Request
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class EddieMerlotsUSSpider(StructuredDataSpider):
    name = "eddie_merlots_us"
    item_attributes = {"brand": "Eddie Merlot's"}
    start_urls = ["https://www.eddiemerlots.com/location-search/"]
    wanted_types = ["Restaurant"]

    def parse(self, response: Response) -> Iterable[Request]:
        yield from response.follow_all(
            xpath='//div[@class="locationlinks"]/a[normalize-space(.)="More Details"]', callback=self.parse_sd
        )

    def pre_process_data(self, ld_data: dict, **kwargs) -> None:
        address = ld_data["address"]
        street, city, state, postcode = re.fullmatch(
            r"(.+),\s*([^,]+),\s*([A-Z]{2})\s+(\d{5})", address["streetAddress"].strip()
        ).groups()
        address.update(streetAddress=street, addressLocality=city, addressRegion=state, postalCode=postcode)

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["ref"] = response.url.rstrip("/").rsplit("/", 1)[-1]
        item["branch"] = unescape(item.pop("name")).removeprefix("Eddie Merlot's ")
        hours = OpeningHours()
        section = response.xpath('//h2[normalize-space(.)="Hours"]/following-sibling::div[1]')
        lines = section.xpath("./p[not(preceding-sibling::h6)]")
        if not lines:
            lines = section.xpath('./p[preceding-sibling::h6[1][normalize-space(.)="DINNER"]]')
        for line in lines:
            hours.add_ranges_from_string(" ".join(line.css(".txt::text").getall()))
        item["opening_hours"] = hours
        apply_category(Categories.RESTAURANT, item)
        yield item
