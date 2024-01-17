import re

import scrapy

from locations.categories import apply_category
from locations.items import Feature


class CompletudeSpider(scrapy.Spider):
    name = "completude"
    item_attributes = {"brand": "Complétude", "brand_wikidata": "Q2990589"}
    allowed_domains = ["completude.com"]
    start_urls = ["https://www.completude.com/mon-agence/"]

    def parse(self, response):
        urls = response.xpath('//ul[@class="list-link-items list-link-items--alt"]/li/a/@href').extract()

        for url in urls:
            yield scrapy.Request(response.urljoin(url), callback=self.parse_location)

    def parse_location(self, response):
        ref = re.search(r".+/(.+)", response.url).group(1)

        try:
            address_data = response.xpath('//div[@class="location__body"]/p/text()').extract()
            city_postal = address_data.pop(-1)
            city, postal = re.search(r"\s+(.*)(\d{5})", city_postal).groups()

            properties = {
                "ref": ref.strip("/"),
                "street_address": address_data[0].strip(),
                "city": city,
                "postcode": postal,
                "phone": response.xpath('//ul[@class="list-contacts"]/li[1]/a/span/text()').extract_first(),
                "name": response.xpath('//select[@name="agency"]/option[2]/text()').extract_first(),
                "country": "FR",
                "lat": float(response.xpath('//div[@class="google-map map-default"]/@data-lat').extract_first()),
                "lon": float(response.xpath('//div[@class="google-map map-default"]/@data-lng').extract_first()),
                "website": response.url,
            }

            apply_category({"office": "tutoring"}, properties)
            yield Feature(**properties)
        except:
            pass
