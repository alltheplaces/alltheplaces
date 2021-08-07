import json
import re

import scrapy
from scrapy.selector import Selector

from locations.hours import OpeningHours
from locations.items import GeojsonPointItem


class TropicalSmoothieCafe(scrapy.Spider):
    name = "tropical_smoothie_cafe"
    item_attributes = {"brand": "Tropical Smoothie Cafe", "brand_wikidata": "Q7845817"}
    allowed_domains = ["locations.tropicalsmoothiecafe.com"]
    start_urls = ("https://locations.tropicalsmoothiecafe.com/sitemap.xml",)

    def parse(self, response):
        xml = Selector(response)
        xml.remove_namespaces()

        urls = xml.xpath("//loc/text()").extract()
        urls = [url.strip() for url in urls]
        for url in urls:
            path = scrapy.utils.url.parse_url(url).path
            if re.match(r"^/.*/.*/.*$", path):
                yield scrapy.Request(url, callback=self.parse_location)

    def parse_location(self, response):
        hours_spec = response.css(".Cafe-hours").xpath(".//@data-days").get()
        hours = self.parse_hours(json.loads(hours_spec)) if hours_spec else None
        ref = (
            response.css(
                """
            a.Header-orderOnline[href^="https://ordernow.tropicalsmoothie.com"],
            a.Header-orderOnline[href^="https://order.tropicalsmoothie.com"],
            a.Header-orderOnline[href^="https://order.tropicalsmoothiecafe.com"]
            """
            )
            .attrib["href"]
            .split("/")[-1]
        )

        properties = {
            "name": response.xpath('//h1[@itemprop="name"]/text()').get(),
            "extras": {"branch": response.css("div.Hero-city").xpath("./text()").get()},
            "addr_full": response.xpath(
                '//*[@itemprop="streetAddress"]/@content'
            ).get(),
            "city": response.xpath('//*[@itemprop="addressLocality"]/@content').get(),
            "state": response.xpath('//*[@itemprop="addressRegion"]/text()').get(),
            "postcode": response.xpath('//*[@itemprop="postalCode"]/text()').get(),
            "phone": response.xpath('//*[@itemprop="telephone"]/text()').get(),
            "website": response.url,
            "opening_hours": hours,
            "ref": ref,
            "lat": response.xpath('//*[@itemprop="latitude"]/@content').get(),
            "lon": response.xpath('//*[@itemprop="longitude"]/@content').get(),
        }
        yield GeojsonPointItem(**properties)

    def parse_hours(self, hours_json):
        opening_hours = OpeningHours()
        for date in hours_json:
            day = date["day"][:2].capitalize()
            for interval in date["intervals"]:
                start_hr, start_min = divmod(interval["start"], 100)
                end_hr, end_min = divmod(interval["end"], 100)
                opening_hours.add_range(
                    day, f"{start_hr}:{start_min}", f"{end_hr}:{end_min}"
                )
        return opening_hours.as_opening_hours()
