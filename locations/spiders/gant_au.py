import re
from typing import Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature


class GantAUSpider(Spider):
    name = "gant_au"
    item_attributes = {"brand": "GANT", "brand_wikidata": "Q1493667"}
    allowed_domains = ["gant.com.au"]
    start_urls = ["https://gant.com.au/pages/stores-1"]

    def parse(self, response: Response) -> Iterable[Feature]:
        for location in response.xpath('//div[contains(@class, "stores-data")]/div'):
            properties = {
                "ref": location.xpath('./p[@class = "name"]/text()')
                .get()
                .replace('"', "")
                .replace(" ", "_")
                .lower()
                .strip(),
            }
            field_map = {
                "state": "state",
                "name": "branch",
                "address": "addr_full",
                "phone": "phone",
                "coords-lat": "lat",
                "coords-long": "lon",
            }
            for field_source, field_mapped in field_map.items():
                properties[field_mapped] = (
                    location.xpath(f'./p[@class = "{field_source}"]/text()').get().replace('"', "").strip()
                )

            properties["opening_hours"] = OpeningHours()
            hours_string = ""
            hours_ranges = location.xpath('./p[@class = "hours"]/text()').get().split(r"\n")
            for hours_range in hours_ranges:
                if m1 := re.search(
                    r"((?:(?:MON|TUE|WED|THU|FRI|SAT|SUN)\s*-\s*(?:MON|TUE|WED|THU|FRI|SAT|SUN)|(?:MON|TUE|WED|THU|FRI|SAT|SUN)))",
                    hours_range.upper(),
                ):
                    if m2 := re.search(
                        r"((?:CLOSED|\d{1,2}(?:[:\.]\d{2})?\s*[AP]M\s*-\s*\d{1,2}(?:[:\.]\d{2})?\s*[AP]M))",
                        hours_range.upper(),
                    ):
                        hours_string = hours_string + " " + m1.group(1) + ": " + m2.group(1)
            properties["opening_hours"].add_ranges_from_string(hours_string)

            apply_category(Categories.SHOP_CLOTHES, properties)
            yield Feature(**properties)
