import re

import scrapy

from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class JasonsDeliSpider(scrapy.Spider):
    name = "jasonsdeli"
    item_attributes = {"brand": "Jason's Deli", "brand_wikidata": "Q16997641"}
    allowed_domains = ["jasonsdeli.com"]
    start_urls = ("https://www.jasonsdeli.com/restaurants",)

    def parse_hours(self, elements):
        opening_hours = OpeningHours()

        for item in elements:
            if m := re.search(
                r"([a-z]+):.([0-9:\sAPM]+)\s-\s([0-9:\sAPM]+)",
                item,
                flags=re.IGNORECASE,
            ):
                opening_hours.add_range(m.group(1), m.group(2), m.group(3), time_format="%I:%M %p")
        return opening_hours.as_opening_hours()

    def parse_store(self, response):
        ref = re.search(r".+/(.+)", response.url).group(1)

        properties = {
            "addr_full": merge_address_lines(response.xpath('//div[@class="address"]/text()').getall()),
            "city": response.xpath('//div[@class="address"]/text()').extract()[-1].split(",")[0],
            "state": response.xpath('//div[@class="address"]/text()').extract()[-1].split(", ")[1].split(" ")[-2],
            "postcode": response.xpath('//div[@class="address"]/text()').extract()[-1].split(", ")[1].split(" ")[-1],
            "ref": ref,
            "website": response.url,
            "phone": response.xpath('//a[@class="cnphone"]/text()').extract_first(),
        }

        hours = self.parse_hours(response.xpath('//div[@class="loc-hours"]/p/text()').extract())

        try:
            bus_name = response.xpath('//div[@class="loc-title"]/text()').extract()[0].split(": ")[1]
        except IndexError:
            bus_name = response.xpath('//div[@class="loc-title"]/text()').extract_first()
        properties["name"] = bus_name

        if hours:
            properties["opening_hours"] = hours

        if m := re.search(r'"center":\{"lat":"(-?\d+\.\d+)","lon":"(-?\d+\.\d+)"', response.text):
            properties["lat"], properties["lon"] = m.groups()

        yield Feature(**properties)

    def parse(self, response):
        urls = response.xpath('//span[@class="field-content"]/a/@href').extract()

        for url in urls:
            yield scrapy.Request(response.urljoin(url), callback=self.parse_store)
