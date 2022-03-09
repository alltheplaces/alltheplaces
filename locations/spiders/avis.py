import scrapy
import re

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


DAY_MAPPING = {
    "Mon": "Mo",
    "Tue": "Tu",
    "Wed": "We",
    "Thu": "Th",
    "Fri": "Fr",
    "Sat": "Sa",
    "Sun": "Su",
}
DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


class AvisSpider(scrapy.Spider):

    name = "avis"
    item_attributes = {"brand": "Avis", "brand_wikidata": "Q791136"}
    download_delay = 0.5
    allowed_domains = [
        "avis.com",
    ]
    start_urls = ("https://www.avis.com/en/locations/avisworldwide",)

    def parse_hours(self, hours):
        "Sun - Sat 7:00 AM - 10:00 PM"
        opening_hours = OpeningHours()
        hours = [h.strip() for h in hours.split(";")]

        for hour in hours:
            if hour == "Sun - Sat open 24 hrs":
                return "24/7"
            range_match = re.search(
                r"([A-Za-z]{3})\s-\s([A-Za-z]{3})\s([\d:\sAMP]+)\s-\s([\d:\sAMP]+)",
                hour,
            )
            if range_match:
                start_day, end_day, start_time, end_time = range_match.groups()
            else:
                single_match = re.search(
                    r"([A-Za-z]{3})\s([\d:\sAMP]+)\s-\s([\d:\sAMP]+)", hour
                )
                if not single_match:
                    continue
                start_day, start_time, end_time = single_match.groups()
                end_day = start_day

            for day in DAYS[DAYS.index(start_day) : DAYS.index(end_day) + 1]:
                opening_hours.add_range(
                    day=DAY_MAPPING[day],
                    open_time=start_time.strip(),
                    close_time=end_time.strip(),
                    time_format="%I:%M %p",
                )
        return opening_hours.as_opening_hours()

    def parse_store(self, response):
        if response.url == "https://www.avis.com/en/error/500":
            # some closed locations get redirected to this error page
            return

        def clean(val):
            if val:
                return val.strip(", ")
            return val

        ref = response.url.split("/")[-1]

        latitude = None
        longitude = None

        if (
            response.xpath('//meta[@itemprop="latitude"]/@content').extract_first()
            is not None
        ):
            latitude = float(
                response.xpath('//meta[@itemprop="latitude"]/@content').extract_first()
            )

        if (
            response.xpath('//meta[@itemprop="longitude"]/@content').extract_first()
            is not None
        ):
            longitude = float(
                response.xpath('//meta[@itemprop="longitude"]/@content').extract_first()
            )

        properties = {
            "name": clean(
                response.xpath('//h2/span[@itemprop="name"]/text()').extract_first()
            ),
            "addr_full": clean(
                response.xpath(
                    'normalize-space(//span[@itemprop="streetAddress"]/text())'
                ).extract_first()
            ),
            "phone": response.xpath(
                'normalize-space(//span[@itemprop="telephone"]/text())'
            ).extract_first(),
            "city": clean(
                response.xpath(
                    'normalize-space(//span[@itemprop="addressLocality"]/text())'
                ).extract_first()
            ),
            "state": clean(
                response.xpath(
                    'normalize-space(//span[@itemprop="addressRegion"]/text())'
                ).extract_first()
            ),
            "postcode": clean(
                response.xpath(
                    'normalize-space(//span[@itemprop="postalCode"]/text())'
                ).extract_first()
            ),
            "country": clean(
                response.xpath(
                    'normalize-space(//span[@itemprop="addressCountry"]/text())'
                ).extract_first()
            ),
            "ref": ref,
            "website": response.url,
            "lat": latitude,
            "lon": longitude,
        }
        hours = response.xpath(
            '//meta[@itemprop="openingHours"]/@content'
        ).extract_first()
        if hours:
            properties["opening_hours"] = self.parse_hours(hours)
        yield GeojsonPointItem(**properties)

    def parse_state(self, response):
        urls = response.xpath(
            '//ul[contains(@class, "location-list-ul")]//li/a/@href'
        ).extract()

        if not urls:
            urls = set(
                response.xpath(
                    '//ul[contains(@class, "LocContainer")]//a/@href'
                ).extract()
            )
            urls = [u for u in urls if "javascript:void" not in u]

        location_list = re.compile("^/en/locations/(?:us|ca|au)/[a-z]{2}/[^/]+$")
        us_single_location = re.compile(
            r"/en/locations/(?:us|ca|au)/[a-z]{2}/[^/]+/[^/]+$"
        )
        single_location = re.compile(r"/en/locations/(?!us|ca|au)[a-z]{2}/[^/]+/[^/]+$")

        for url in urls:
            if single_location.match(url) or us_single_location.match(url):
                yield scrapy.Request(response.urljoin(url), callback=self.parse_store)
            elif location_list.match(url):
                # skip these, we get them already
                continue
            elif "xx" in url:
                continue

    def parse_country(self, response):
        urls = response.xpath(
            '//div[contains(@class,"country-wrapper")]//li/a/@href'
        ).extract()

        for url in urls:
            yield scrapy.Request(response.urljoin(url), callback=self.parse_state)

    def parse(self, response):
        urls = response.xpath('//div[@class="wl-location-state"]//li/a/@href').extract()

        for url in urls:
            yield scrapy.Request(response.urljoin(url), callback=self.parse_country)
