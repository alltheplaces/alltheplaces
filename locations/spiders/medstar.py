import json

import scrapy

from locations.categories import Categories, apply_category
from locations.items import Feature


class MedstarSpider(scrapy.Spider):
    # download_delay = 0.2
    name = "medstar"
    item_attributes = {"brand": "Medstar Health", "brand_wikidata": "Q6804943"}
    allowed_domains = ["www.medstarhealth.org"]
    start_urls = (
        "https://www.medstarhealth.org//sxa/search/results/?s={3D6661A6-0F00-4C7C-A8E9-6E8F15B6528B}&itemid={EB24C2F5-4CC8-4C57-8505-D865C498C3ED}&sig=locationsearch&distance%20by%20miles=250000000&p=500&o=Navigation%20Title%2CAscending&v=%7B1844930B-B644-4B06-84D9-68B7F7EDE9A0%7D",
    )

    def parse(self, response):
        data = json.loads(response.text)
        for i in data["Results"]:
            url = i["Url"]
            yield scrapy.Request(response.urljoin(url), callback=self.parse_loc)

    def parse_loc(self, response):
        try:
            phone = response.xpath('//div[@class="field-phone-number"]/a/@href').extract()[0].replace("tel:", "")
        except:
            phone = ""

        properties = {
            "ref": response.url.split("/")[-1],
            "name": response.xpath('//h1[@class="field-title"]/text()').extract()[0],
            "addr_full": response.xpath('//div[@class="field-address"][1]/text()').extract()[0]
            + ", "
            + response.xpath('//div[@class="field-city"]/text()').extract()[0],
            "country": "US",
            "phone": phone,
            "lat": float(response.xpath('//div[@class="field-distance fieldlocation "]/span/@data-lat').extract()[0]),
            "lon": float(response.xpath('//div[@class="field-distance fieldlocation "]/span/@data-lon').extract()[0]),
        }

        name_lower = properties.get("name").lower()
        if "hospital" in name_lower:
            apply_category(Categories.HOSPITAL, properties)
        elif "pharmacy" in name_lower:
            apply_category(Categories.PHARMACY, properties)
        elif self.list_check(["medical center", "hospital center"], name_lower):
            apply_category({"healthcare": "centre"}, properties)
        elif self.list_check(["urgent care", "women's health"], name_lower):
            apply_category(Categories.CLINIC, properties)

        yield Feature(**properties)

    def list_check(self, substr_list, string):
        for substr in substr_list:
            if substr in string:
                return True
        else:
            return False
