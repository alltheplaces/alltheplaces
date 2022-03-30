import datetime
import re

import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


DAY_MAPPING = {
    "Monday": "Mo",
    "Tuesday": "Tu",
    "Wednesday": "We",
    "Thursday": "Th",
    "Friday": "Fr",
    "Saturday": "Sa",
    "Sunday": "Su",
}


class PapaMurphysSpider(scrapy.Spider):

    name = "papamurphys"
    item_attributes = {"brand": "Papa Murphy's"}
    allowed_domains = ["papamurphys.com"]
    download_delay = 0.5
    start_urls = ("https://order.papamurphys.com/locations",)

    def parse_hours(self, elem):
        days = elem.xpath(".//dt/text()").extract()
        hours = elem.xpath(".//dd/text()").extract()

        opening_hours = OpeningHours()
        for d, h in zip(days, hours):
            day = DAY_MAPPING[d.replace(":", "")]
            try:
                open_time, close_time = h.split("-")
            except ValueError:
                continue
            if ":" in open_time:
                open_time = datetime.datetime.strptime(open_time, "%I:%M%p").strftime(
                    "%H:%M"
                )
            else:
                open_time = datetime.datetime.strptime(open_time, "%I%p").strftime(
                    "%H:%M"
                )

            if ":" in close_time:
                close_time = datetime.datetime.strptime(close_time, "%I:%M%p").strftime(
                    "%H:%M"
                )
            else:
                close_time = datetime.datetime.strptime(close_time, "%I%p").strftime(
                    "%H:%M"
                )

            opening_hours.add_range(day=day, open_time=open_time, close_time=close_time)

        return opening_hours.as_opening_hours()

    def parse_stores(self, response):
        properties = {
            "addr_full": response.xpath(
                '//div[@class="streetaddress"]//span[@class="street-address"]/text()'
            ).extract_first(),
            "phone": response.xpath(
                '(//dl[@class="MenuInfo"]/dd/span[@class="tel"]/text())'
            )
            .extract_first()
            .strip(),
            "city": response.xpath(
                '//div[@class="streetaddress"]//span[@class="locality"]/text()'
            ).extract_first(),
            "state": response.xpath(
                '//div[@class="streetaddress"]//span[@class="region"]/text()'
            ).extract_first(),
            "postcode": response.xpath(
                '//div[@class="streetaddress"]//span[@class="postal-code"]/text()'
            ).extract_first(),
            "country": "US",
            "ref": response.url.split("/")[-1],
            "website": response.url,
            "lat": float(
                response.xpath(
                    '//meta[@property="og:latitude"]/@content'
                ).extract_first()
            ),
            "lon": float(
                response.xpath(
                    '//meta[@property="og:longitude"]/@content'
                ).extract_first()
            ),
            "name": response.xpath(
                '//meta[@property="og:title"]/@content'
            ).extract_first(),
        }
        hours = self.parse_hours(response.xpath('//div[@data-hour-type="business"]/dl'))

        if hours:
            properties["opening_hours"] = hours

        yield GeojsonPointItem(**properties)

    def parse_state_stores(self, response):
        stores = response.xpath(
            '//ul[@id="ParticipatingRestaurants"]//li//a/@href'
        ).extract()
        for store in stores:
            yield scrapy.Request(response.urljoin(store), callback=self.parse_stores)

    def parse(self, response):
        urls = response.xpath('//ul[@id="ParticipatingStates"]/li/a/@href').extract()
        for path in urls:
            yield scrapy.Request(
                response.urljoin(path), callback=self.parse_state_stores
            )
