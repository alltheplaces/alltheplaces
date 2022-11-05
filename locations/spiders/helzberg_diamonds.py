import json
import re

import scrapy

from locations.hours import DAYS, OpeningHours
from locations.items import GeojsonPointItem


class HelzbergDiamondsSpider(scrapy.Spider):
    name = "helzberg_diamonds"
    item_attributes = {"brand": "Helzberg Diamonds", "brand_wikidata": "Q16995161"}
    allowed_domains = ["stores.helzberg.com"]
    start_urls = ("https://stores.helzberg.com/sitemap.xml",)

    def parse(self, response):
        response.selector.remove_namespaces()
        locations = response.xpath("//url/loc/text()").getall()
        for url in locations:
            if url.endswith(".html"):
                yield scrapy.Request(url, callback=self.parse_store)

    def parse_store(self, response):
        data = json.loads(
            response.xpath('//script[@type="application/ld+json"]/text()').get()
        )[0]
        ref = re.search(r"jewelry-store-(\d+).html", data["url"])[1]
        properties = {
            "ref": ref,
            "lat": data["geo"]["latitude"],
            "lon": data["geo"]["longitude"],
            "name": data["name"],
            "addr_full": data["address"]["streetAddress"],
            "city": data["address"]["addressLocality"],
            "state": data["address"]["addressRegion"],
            "postcode": data["address"]["postalCode"],
            "phone": data["address"]["telephone"],
            "website": response.url,
            "opening_hours": self.parse_hours(data["openingHours"]),
        }
        yield GeojsonPointItem(**properties)

    def parse_hours(self, hours):
        opening_hours = OpeningHours()
        groups = re.findall(rf'(({"|".join(DAYS)}) \S+ - \S+)', hours)
        for (g, _) in groups:
            day, open, _, close = g.split()
            opening_hours.add_range(day, open, close)
        return opening_hours.as_opening_hours()
