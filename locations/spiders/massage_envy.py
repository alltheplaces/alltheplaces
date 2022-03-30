import re
import scrapy
from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class MassageEnvySpider(scrapy.Spider):

    name = "massage_envy"
    item_attributes = {"brand": "Massage Envy"}
    allowed_domains = ["locations.massageenvy.com"]
    start_urls = ("https://locations.massageenvy.com/index.html",)

    def parse_hours(self, hours):
        opening_hours = OpeningHours()
        for group in hours:
            if "Closed" in group:
                pass
            else:
                days, open_time, close_time = re.search(
                    r"([a-zA-Z,]+)\s([\d:]+)-([\d:]+)", group
                ).groups()
                days = days.split(",")
                for day in days:
                    opening_hours.add_range(
                        day=day,
                        open_time=open_time,
                        close_time=close_time,
                        time_format="%H:%M",
                    )

        return opening_hours.as_opening_hours()

    def parse(self, response):
        urls = response.xpath(
            '//a[@class="c-directory-list-content-item-link"]/@href | //a[@class="c-location-grid-item-link"]/@href | //a[@class="location-info-link store-details"]/@href'
        ).extract()
        # If cannot find 'c-directory-list-content-item-link' or 'c-location-grid-item-link' then this is a store page
        if len(urls) == 0:
            properties = {
                "name": response.xpath(
                    '//*[@class="location-name h1-normal"]/text()'
                ).extract_first(),
                "addr_full": response.xpath(
                    '//*[@class="c-address-street-1"]/text()'
                ).extract_first(),
                "city": response.xpath(
                    '//*[@itemprop="addressLocality"]/text()'
                ).extract_first(),
                "state": response.xpath(
                    '//*[@itemprop="addressRegion"]/text()'
                ).extract_first(),
                "postcode": response.xpath(
                    '//*[@itemprop="postalCode"]/text()'
                ).extract_first(),
                "country": response.xpath(
                    '//*[@itemprop="addressCountry"]/text()'
                ).extract_first(),
                "phone": response.xpath('//*[@id="phone-main"]/text()').extract_first(),
                "ref": "_".join(
                    re.search(
                        r".+/(.+?)/(.+?)/(.+?)/?(?:\.html|$)", response.url
                    ).groups()
                ),
                "website": response.url,
                "lat": response.xpath(
                    '//*[@itemprop="latitude"]/@content'
                ).extract_first(),
                "lon": response.xpath(
                    '//*[@itemprop="longitude"]/@content'
                ).extract_first(),
            }

            hours = self.parse_hours(
                response.xpath('//*[@itemprop="openingHours"]/@content').extract()
            )
            if hours:
                properties["opening_hours"] = hours

            yield GeojsonPointItem(**properties)
        else:
            for path in urls:
                yield scrapy.Request(url=response.urljoin(path), callback=self.parse)
