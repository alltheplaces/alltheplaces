import json
import re

import scrapy

from locations.categories import Categories
from locations.items import Feature


class RegisSalonSpider(scrapy.Spider):
    name = "regis_salon"
    item_attributes = {"brand": "Regis", "brand_wikidata": "Q7309325", "extras": Categories.SHOP_HAIRDRESSER.value}
    allowed_domains = ["www.regissalons.com"]
    start_urls = ["https://www.regissalons.com/salon-locator.html"]

    def parse(self, response):
        for href in response.xpath('//@href[contains(., "/locations/")]').extract():
            yield scrapy.Request(response.urljoin(href), callback=self.parse_store)

    def parse_store(self, response):
        script = response.xpath('//script[contains(text(), "wpslMap_0")]/text()').get()
        json_txt = re.search("wpslMap_0 = (.*);$", script, re.M)[1]
        data = json.loads(json_txt)["locations"][0]
        # decode entities
        name = scrapy.Selector(text=data["store"]).xpath("//text()").get()
        phone = response.xpath('//@href[contains(., "tel:")]').extract_first().replace("tel:", "")
        properties = {
            "lat": data["lat"],
            "lon": data["lng"],
            "ref": data["id"],
            "name": name,
            "website": response.url,
            "street_address": data["address2"],
            "city": data["city"],
            "state": data["state"],
            "postcode": data["zip"],
            "country": data["country"],
            "phone": phone,
        }
        yield Feature(**properties)
