import json
import re

import scrapy

from locations.items import Feature


class UniversityMarylandMedicalSystemSpider(scrapy.Spider):
    name = "university_maryland_medical_system"
    item_attributes = {"brand": "University of Maryland Medical System"}
    allowed_domains = ["www.umms.org"]
    start_urls = ["https://www.umms.org/locations"]

    def parse(self, response):
        template = (
            "https://www.umms.org/locations?page=1&perpage=50&q=&serv={path}&sort=Ascending&view=list&st=Locations"
        )
        paths = response.xpath('//select[@class="select-search__select"]//option/@value').extract()

        for path in paths:
            yield scrapy.Request(url=template.format(path=path), callback=self.parse_list)

    def parse_list(self, response):
        list_urls = response.xpath('//li[@class="search-results__item u-cf"]/div[2]/div/a[1]/@href').extract()

        for url in list_urls:
            yield scrapy.Request(response.urljoin(url), callback=self.parse_location)

    def parse_location(self, response):
        data = json.loads(response.xpath('//div[contains(@class, "locations")]/@data-map-json').extract_first())
        addr_last_line = data["items"][0]["address2"]
        city, state, zipcode = re.search(
            r"^(.*),\s+([a-z]{2}|Maryland)\s+([0-9]+)$", addr_last_line, re.IGNORECASE
        ).groups()

        ref = "_".join(re.search(r".+/(.+)/.+/(.+)", response.url).groups())

        properties = {
            "name": data["items"][0]["title"],
            "ref": ref,
            "addr_full": data["items"][0]["address1"],
            "city": city,
            "state": state,
            "postcode": zipcode,
            "phone": data["items"][0]["phone"],
            "website": response.url,
            "lat": float(data["items"][0]["coordinates"][0]["lat"]),
            "lon": float(data["items"][0]["coordinates"][0]["lng"]),
        }
        yield Feature(**properties)
