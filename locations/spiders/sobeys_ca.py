import json
import re
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours, sanitise_day
from locations.items import Feature


class SobeysCASpider(Spider):
    name = "sobeys_ca"
    item_attributes = {"brand": "Sobeys", "brand_wikidata": "Q1143340"}
    allowed_domains = ["www.sobeys.com"]
    start_urls = [
        "https://www.sobeys.com/store-locator/",
        "https://liquor.sobeys.com/store-locator/",
        "https://sobeyspharmacy.com/store-locator/",
    ]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.xpath('//div[@class="store-result "]'):
            properties = {
                "ref": store.xpath(".//@data-id").get(),
                "branch": store.xpath('.//span[@class="name"]/text()')
                .get()
                .removeprefix("Sobeys")
                .removesuffix("Sobeys")
                .strip(),
                "lat": store.xpath(".//@data-lat").get(),
                "lon": store.xpath(".//@data-lng").get(),
                "street_address": store.xpath('.//span[@class="location_address_address_1"]/text()').get(),
                "city": store.xpath('.//span[@class="city"]/text()').get(),
                "state": store.xpath('.//span[@class="province"]/text()').get(),
                "postcode": store.xpath('.//span[@class="postal_code"]/text()').get(),
                "phone": store.xpath('.//span[@class="phone"]/a/text()').get(),
                "website": store.xpath('.//a[@class="store-title"]/@href').get(),
            }
            try:
                properties["opening_hours"] = self.parse_opening_hours(json.loads(store.xpath(".//@data-hours").get()))
            except Exception as e:
                self.logger.error("Error parsing opening hours {} {}".format(e, properties["ref"]))

            if "www.sobeys.com" in response.url:
                apply_category(Categories.SHOP_SUPERMARKET, properties)
            elif "liquor.sobeys.com" in response.url:
                apply_category(Categories.SHOP_ALCOHOL, properties)
            elif "sobeyspharmacy.com" in response.url:
                apply_category(Categories.PHARMACY, properties)

            yield Feature(**properties)

    def parse_opening_hours(self, rules: dict) -> OpeningHours:
        oh = OpeningHours()
        for day, times in rules.items():
            if not times:
                continue
            if day := sanitise_day(day):
                if times.upper() == "CLOSED":
                    oh.set_closed(day)
                else:
                    start_time, end_time = re.split(r"to|-", times.replace(" ", "").replace(".", ""))
                    oh.add_range(day, start_time, end_time, "%I:%M%p")
        return oh
