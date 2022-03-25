import scrapy
import re

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class FifthThirdBankSpider(scrapy.Spider):

    name = "fifththirdbank"
    item_attributes = {"brand": "Fifth Third Bank"}
    download_delay = 0.5
    allowed_domains = [
        "53.com",
    ]
    start_urls = ("https://locations.53.com/index.html",)

    def parse_hours(self, hours):
        opening_hours = OpeningHours()
        for hour in hours:
            day, hours = re.search(r"([a-z]{2})\s(.*)", hour, re.IGNORECASE).groups()
            if hours == "Closed":
                continue
            open_time, close_time = hours.split("-")
            opening_hours.add_range(day, open_time=open_time, close_time=close_time)

        return opening_hours.as_opening_hours()

    def parse_branch(self, response):
        ref = re.findall(r".com/(.+?)/(.+?)/(.+?).html", response.url)[0]
        ref = "_".join(ref)

        name = response.xpath(
            'normalize-space(//h1[@class="c-location-title"]/span[@class="name"]/text())'
        ).extract_first()
        branch = response.xpath(
            'normalize-space(//h1[@class="c-location-title"]/span[@class="geomodifier"]/text())'
        ).extract_first()

        properties = {
            "name": " ".join([name, branch]),
            "addr_full": response.xpath(
                'normalize-space(//span[@itemprop="streetAddress"]/text())'
            ).extract_first(),
            "city": response.xpath(
                'normalize-space(//span[@itemprop="addressLocality"]/text())'
            ).extract_first(),
            "state": response.xpath(
                'normalize-space(//span[@itemprop="addressRegion"]/text())'
            ).extract_first(),
            "postcode": response.xpath(
                'normalize-space(//span[@itemprop="postalCode"]/text())'
            ).extract_first(),
            "phone": response.xpath(
                'normalize-space(//span[@itemprop="telephone"]/text())'
            ).extract_first(),
            "ref": ref,
            "website": response.url,
            "lat": float(
                response.xpath(
                    'normalize-space(//meta[@itemprop="latitude"]/@content)'
                ).extract_first()
            ),
            "lon": float(
                response.xpath(
                    'normalize-space(//meta[@itemprop="longitude"]/@content)'
                ).extract_first()
            ),
        }
        hours = response.xpath('//tr[@itemprop="openingHours"]/@content').extract()
        if hours:
            properties["opening_hours"] = self.parse_hours(hours)
        yield GeojsonPointItem(**properties)

    def parse(self, response):
        branch_urls = response.xpath(
            '//div[@class="location"]//a[@class="location-name-link"]/@href'
        ).extract()
        if branch_urls:
            for url in branch_urls:
                yield scrapy.Request(response.urljoin(url), callback=self.parse_branch)

        else:
            urls = response.xpath(
                '//div[@class="c-directory-list"]//li/a/@href'
            ).extract()

            for url in urls:
                if len(url.split("/")) == 3:
                    # if there's only one branch in a city then the url is directly to that branch page
                    yield scrapy.Request(
                        response.urljoin(url), callback=self.parse_branch
                    )
                else:
                    yield scrapy.Request(response.urljoin(url))
