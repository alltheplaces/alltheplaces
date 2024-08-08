import re

import scrapy

from locations.hours import DAYS_3_LETTERS, OpeningHours
from locations.items import Feature


class YmcaSpider(scrapy.Spider):
    name = "ymca"
    item_attributes = {"brand": "YMCA", "brand_wikidata": "Q157169"}
    allowed_domains = ["ymca.org"]
    download_delay = 0.5
    start_urls = (
        "https://www.ymca.org/sitemap.xml?page=1",
        "https://www.ymca.org/sitemap.xml?page=2",
    )

    def parse(self, response):
        response.selector.remove_namespaces()
        all_urls = response.xpath("//url/loc/text()").extract()
        # Fix URLs and filter out blogs, etc at the same time
        ymca_urls = [
            url.replace("http://national/", "https://www.ymca.org/") for url in all_urls if "locations/" in url
        ]
        for url in ymca_urls:
            # As of 2021-10-25, this URL 500's consistently
            if url == "https://www.ymca.org/locations/skyview-ymca":
                continue
            yield scrapy.Request(url.strip(), callback=self.parse_location)

    def parse_location(self, response):
        geo = response.xpath('//div[contains(@class, "geolocation-location")]')

        yield Feature(
            ref=response.url.split("/")[-1],
            name=response.xpath("//h1/text()").extract_first().strip(),
            lat=float(geo.attrib["data-lat"]),
            lon=float(geo.attrib["data-lng"]),
            addr_full=response.xpath('//span[@class="address-line1"]/text()').extract_first(),
            city=response.xpath('//span[@class="locality"]/text()').extract_first(),
            state=response.xpath('//span[@class="administrative-area"]/text()').extract_first(),
            postcode=response.xpath('//span[@class="postal-code"]/text()').extract_first(),
            country=response.xpath('//span[@class="country"]/text()').extract_first(),
            phone=response.xpath('//div[contains(@class, "field--type-telephone")]//a/text()').extract_first(),
            website=response.url,
            opening_hours=self.parse_hours(
                response.xpath('//div[contains(@class, "field--name-field-branch-hours")]//td/text()').getall()
            ),
        )

    def parse_hours(self, hours):
        opening_hours = OpeningHours()

        days = hours[0::2]
        times = hours[1::2]

        for day_range, time_range in zip(days, times):
            if time_range == "Closed":
                continue

            open_time, close_time = re.sub(r"\s", "", time_range).split("-")

            # Day range, e.g. Mon - Fri
            if "-" in day_range:
                start_day, end_day = re.sub(r"[\s:]", "", day_range).split("-")
                for day in DAYS_3_LETTERS[
                    DAYS_3_LETTERS.index(start_day[0:3]) : DAYS_3_LETTERS.index(end_day[0:3]) + 1
                ]:
                    opening_hours.add_range(
                        day=day[0:2],
                        open_time=open_time,
                        close_time=close_time,
                        time_format="%I:%M%p",
                    )
            # Single day, e.g. Sat
            else:
                opening_hours.add_range(
                    day=day_range[0:2],
                    open_time=open_time,
                    close_time=close_time,
                    time_format="%I:%M%p",
                )

        return opening_hours.as_opening_hours()
