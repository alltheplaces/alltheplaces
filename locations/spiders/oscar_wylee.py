import re
from html import unescape

from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.google_url import extract_google_position
from locations.hours import OpeningHours
from locations.items import Feature


class OscarWyleeSpider(CrawlSpider):
    name = "oscar_wylee"
    item_attributes = {"brand": "Oscar Wylee", "brand_wikidata": "Q120669494"}
    allowed_domains = [
        "www.oscarwylee.com.au",
        "www.oscarwylee.co.nz",
    ]
    start_urls = [
        "https://www.oscarwylee.com.au/locations/full-store-list.html",
        "https://www.oscarwylee.co.nz/locations/full-store-list.html",
    ]
    rules = [
        Rule(LinkExtractor(allow=r"/locations/(?!full-store-list\.html).+\.html$"), callback="parse"),
    ]

    def parse(self, response):
        properties = {
            "ref": response.url,
            "name": response.xpath('//h1[@class="static-location-header"]/text()')
            .get()
            .replace("Optometrist", "")
            .strip(),
            "addr_full": unescape(
                re.sub(
                    r"\s+", " ", " ".join(filter(None, response.xpath('//p[@class="short-content"]//text()').getall()))
                )
            ).strip(),
            "website": response.url,
        }
        if ".com.au" in response.url:
            properties["country"] = "AU"
        elif ".co.nz" in response.url:
            properties["country"] = "NZ"
        extract_google_position(properties, response)
        hours_string = " ".join(filter(None, response.xpath('//div[@class="store-schedule"]//text()').getall()))
        properties["opening_hours"] = OpeningHours()
        properties["opening_hours"].add_ranges_from_string(hours_string)
        yield Feature(**properties)
