import re

import scrapy

from locations.items import Feature


class FlemingsSteakhouseSpider(scrapy.Spider):
    name = "flemings_steakhouse"
    item_attributes = {
        "brand": "Fleming's Prime Steakhouse & Wine Bar",
        "brand_wikidata": "Q5458552",
    }
    allowed_domains = ["flemingssteakhouse.com"]
    start_urls = ("https://www.flemingssteakhouse.com/locations",)

    def parse(self, response):
        urls = response.xpath('//ul[@class="locations"]/li/a/@href').extract()
        for url in urls:
            yield scrapy.Request(response.urljoin(url), callback=self.parse_location)

    def parse_location(self, response):
        address_element = response.xpath('//p[contains(text(), "Address")]/../p[2]/text()').extract()
        address_element = list(filter(None, [a.strip() for a in address_element]))
        address = address_element[0]
        city_state_postal_element = address_element[1]
        (city, state, postcode) = re.search(r"^(.*), ([A-Z]{2}) (\d{5})$", city_state_postal_element).groups()

        properties = {
            "ref": re.search(r".+/(.+?)/?(?:\.html|$)", response.url).group(1),
            "name": response.xpath('//div[@id="location-details"]/h1/text()').extract_first(),
            "addr_full": address,
            "city": city,
            "state": state,
            "postcode": postcode,
            "website": response.url,
            "phone": response.xpath('//a[@class="phone"]/text()').extract_first(),
        }
        yield Feature(**properties)
