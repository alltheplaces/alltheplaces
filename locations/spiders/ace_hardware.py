import scrapy
import re
import json
from locations.items import GeojsonPointItem
from locations.hours import OpeningHours

DAY_MAPPING = [
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
]


class AceHardwareSpider(scrapy.Spider):
    name = "ace_hardware"
    item_attributes = {"brand": "Ace Hardware", "brand_wikidata": "Q4672981"}
    allowed_domains = ["www.acehardware.com"]
    download_delay = 0.7
    start_urls = ("https://www.acehardware.com/store-directory",)
    user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36"

    def parse_hours(self, lis):
        o = OpeningHours()

        for day in DAY_MAPPING:
            d = day.title()[:2]

            if lis[day]["label"] in ["0000 - 0000", "1201 - 1201"]:
                continue

            o.add_range(d, lis[day]["openTime"], lis[day]["closeTime"])
        return o.as_opening_hours()

    def parse_store(self, response):
        store_data = response.xpath(
            '//script[@id="data-mz-preload-store"]/text()'
        ).extract_first()

        if not store_data:
            return

        store_data = json.loads(store_data)

        properties = {
            "name": store_data["StoreName"],
            "phone": store_data["Phone"],
            "addr_full": store_data["StoreAddressLn1"],
            "city": store_data["StoreCityNm"],
            "state": store_data["StoreStateCd"],
            "postcode": store_data["StoreZipCd"],
            "ref": store_data["StoreNumber"],
            "website": response.url,
            "lat": store_data["Latitude"],
            "lon": store_data["Longitude"],
        }

        hours = self.parse_hours(store_data["RegularHours"])
        if hours:
            properties["opening_hours"] = hours

        yield GeojsonPointItem(**properties)

    def parse(self, response):
        for store_url in (
            response.css("div.store-directory-list-item").xpath("div/a/@href").extract()
        ):
            yield scrapy.Request(response.urljoin(store_url), callback=self.parse_store)
