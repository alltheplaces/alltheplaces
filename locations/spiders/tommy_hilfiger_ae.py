import re
from typing import Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature


class TommyHilfigerAESpider(Spider):
    name = "tommy_hilfiger_ae"
    item_attributes = {"brand": "Tommy Hilfiger", "brand_wikidata": "Q634881"}
    allowed_domains = ["en-ae.tommy.com"]
    start_urls = ["https://en-ae.tommy.com/storelocator"]
    no_refs = True

    def parse(self, response: Response) -> Iterable[Feature]:
        for store in response.xpath('//div[@class="store"]'):
            properties = {
                "branch": store.xpath("./div/div[2]/text()").get(),
                "lat": store.xpath(".//@data-lat").get(),
                "lon": store.xpath(".//@data-long").get(),
                "addr_full": store.xpath("./div/div[3]/text()").get(),
                "phone": store.xpath('.//a[contains(@href, "tel:")]/@href').get().removeprefix("tel:"),
                "opening_hours": OpeningHours(),
            }

            hours_text_raw = re.sub(
                r"\s+", " ", " ".join(store.xpath('.//div[@class="store-opening-hours"]//text()').getall())
            )
            if "PERMANENTLY CLOSED" in hours_text_raw.upper():
                continue
            hours_text_raw = (
                hours_text_raw.replace("12:00 MIDNIGHT", "11:59 PM")
                .replace(" & ", " - ")
                .replace("OPENING HOURS ", "")
                .strip()
            )
            if hours_text_raw.startswith("DAILY ") or hours_text_raw.startswith("WEEKDAYS "):
                properties["opening_hours"].add_ranges_from_string(hours_text_raw)
            else:
                hours_text_clean = ""
                if matches := re.findall(r"(\d+:\d+ [AP]M) - (\d+:\d+ [AP]M) \(([^\)]+)\)", hours_text_raw):
                    for match in matches:
                        hours_text_clean = "{} {}: {} - {}".format(hours_text_clean, match[2], match[0], match[1])
                properties["opening_hours"].add_ranges_from_string(hours_text_clean)

            apply_category(Categories.SHOP_CLOTHES, properties)
            yield Feature(**properties)
