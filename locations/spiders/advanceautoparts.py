import json
import re

import scrapy

from locations.hours import OpeningHours
from locations.items import GeojsonPointItem


class AdvanceautopartsSpider(scrapy.Spider):

    name = "advanceautoparts"
    item_attributes = {"brand": "Advance Auto Parts", "brand_wikidata": "Q4686051"}
    allowed_domains = ["stores.advanceautoparts.com"]
    start_urls = ("https://stores.advanceautoparts.com/sitemap.xml",)

    def parse(self, response):
        response.selector.remove_namespaces()
        for sitemap in response.xpath("//sitemap/loc/text()").extract():
            yield scrapy.Request(sitemap)
        urls = response.xpath("//url/loc/text()").extract()
        storeRe = re.compile(r"^https://stores.advanceautoparts.com/[^/]+/[^/]+/[^/]+$")
        for url in urls:
            if not url.startswith(
                "https://stores.advanceautoparts.com/es"
            ) and storeRe.fullmatch(url):
                yield scrapy.Request(url, callback=self.parse_store)

    def parse_hours(self, store_hours):
        opening_hours = OpeningHours()

        for weekday in store_hours:
            day = weekday.get("day").title()
            for interval in weekday.get("intervals", []):
                open_time = str(interval.get("start"))
                close_time = str(interval.get("end"))
                opening_hours.add_range(
                    day=day[:2],
                    open_time=open_time,
                    close_time=close_time,
                    time_format="%H%M",
                )

        return opening_hours.as_opening_hours()

    def parse_store(self, response):
        name = response.xpath('//h1[@itemprop="name"]/text()').extract_first()

        js = json.loads(response.xpath('//script[@class="js-map-config"]/text()').get())
        ref = js["entities"][0]["profile"]["meta"]["id"]

        hours = response.xpath(
            '//div[@class="c-hours-details-wrapper js-hours-table"]/@data-days'
        ).extract_first()
        try:
            opening_hours = self.parse_hours(json.loads(hours))
        except ValueError:
            opening_hours = None

        properties = {
            "addr_full": response.xpath(
                'normalize-space(//meta[@itemprop="streetAddress"]/@content)'
            ).extract_first(),
            "phone": response.xpath(
                'normalize-space(//div[@itemprop="telephone"]/text())'
            ).extract_first(),
            "city": response.xpath(
                'normalize-space(//meta[@itemprop="addressLocality"]/@content)'
            ).extract_first(),
            "state": response.xpath(
                'normalize-space(//abbr[@itemprop="addressRegion"]/text())'
            ).extract_first(),
            "postcode": response.xpath(
                'normalize-space(//span[@itemprop="postalCode"]/text())'
            ).extract_first(),
            "ref": ref,
            "website": response.url,
            "lat": response.xpath(
                'normalize-space(//meta[@itemprop="latitude"]/@content)'
            ).extract_first(),
            "lon": response.xpath(
                'normalize-space(//meta[@itemprop="longitude"]/@content)'
            ).extract_first(),
            "name": name,
            "opening_hours": opening_hours,
            "extras": {"shop": "car_parts"},
        }
        yield GeojsonPointItem(**properties)
