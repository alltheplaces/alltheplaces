import re

from scrapy import Request, Spider

from locations.hours import OpeningHours
from locations.items import Feature


class HoulihansUSSpider(Spider):
    name = "houlihans_us"
    item_attributes = {"brand": "Houlihan's", "brand_wikidata": "Q5913100s"}
    allowed_domains = ["houlihans.com"]
    start_urls = ["https://houlihans.com/Locations"]
    # Some location pages were observed to redirect back to the location list page.
    custom_settings = {"REDIRECT_ENABLED": False}

    def start_requests(self):
        for url in self.start_urls:
            yield Request(url=url, callback=self.parse_location_urls)

    def parse_location_urls(self, response):
        for location_url in response.xpath('//li[@class="locations"]/a[not(@id="mars")]/@href').getall():
            yield Request(url="https://houlihans.com" + location_url)

    def parse(self, response):
        properties = {
            "ref": response.url,
            "name": re.sub(r"\s+", " ", response.xpath('//h1[@class="loc-name"]/text()').get()).strip(),
            "addr_full": re.sub(
                r"\s+", " ", " ".join(response.xpath('//p[@class="loc-address"]/a/text()').getall())
            ).strip(),
            "phone": response.xpath('//p[@class="loc-phone"]/a/text()').get().strip(),
            "website": response.url,
        }
        hours_string = " ".join(
            filter(None, response.xpath('//p[@class="loc-hours"]/following-sibling::p[not(@*)]').getall())
        )
        properties["opening_hours"] = OpeningHours()
        properties["opening_hours"].add_ranges_from_string(hours_string)
        yield Feature(**properties)
