import re

from scrapy.spiders import SitemapSpider

from locations.hours import DAYS_3_LETTERS, OpeningHours
from locations.items import Feature


class YmcaSpider(SitemapSpider):
    name = "ymca"
    item_attributes = {"brand": "YMCA", "brand_wikidata": "Q157169"}
    allowed_domains = ["ymca.org"]
    sitemap_urls = [
        "https://www.ymca.org/sitemap.xml",
    ]
    sitemap_rules = [(r"locations/", "parse_location")]

    def sitemap_filter(self, entries):
        for entry in entries:
            # To avoid constant redirects
            entry["loc"] = entry["loc"].replace("https://ymca.org/", "https://www.ymca.org/")
            yield entry

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
