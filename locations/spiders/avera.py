import json

import scrapy

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class AveraSpider(scrapy.Spider):
    # download_delay = 0.2
    name = "avera"
    item_attributes = {
        "brand": "Avera",
        "brand_wikidata": "Q4828238",
    }
    allowed_domains = ["www.avera.org"]
    start_urls = ("https://www.avera.org",)

    def parse(self, response):
        url = "https://www.avera.org/locations/search-results/"
        yield scrapy.Request(url=url, callback=self.parse_loc)

    def parse_loc(self, response):
        locs = response.xpath('//div[@class="LocationsList"]//a/@href').extract()
        for loc in locs:
            if loc.startswith("../profile"):
                loc_url = loc.replace("..", "https://www.avera.org/locations")
                yield scrapy.Request(response.urljoin(loc_url), callback=self.parse_data)

        try:
            next_href = "https://www.avera.org" + response.xpath('//a[@class="Next"]/@href').extract_first()
            print(next_href)
            yield scrapy.Request(url=next_href, callback=self.parse_loc)
        except:
            pass


    def parse_data(self, response):
        data = json.loads(
            response.xpath(
                '//script[@type="application/ld+json" and contains(text(), "MedicalBusiness")]/text()'
            ).extract_first()
        )
        item = DictParser.parse(data)
        item["ref"] = data["url"]
        item["image"] = data["image"]
        item["country"] = "US"

        try:
            item["extras"] = {
                "fax": data["faxNumber"]
            }
        except KeyError:
            pass

        oh = OpeningHours()
        oh.from_linked_data(data, time_format="%H:%M:%S")
        item["opening_hours"] = oh.as_opening_hours()

        yield item
