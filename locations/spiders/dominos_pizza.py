import json
import re

import scrapy
from scrapy.selector import Selector

from locations.hours import OpeningHours
from locations.items import Feature

DAY_MAPPING = {
    "Sunday": "Su",
    "Monday": "Mo",
    "Tuesday": "Tu",
    "Wednesday": "We",
    "Thursday": "Th",
    "Friday": "Fr",
    "Saturday": "Sa",
}


class DominosPizzaSpider(scrapy.Spider):
    name = "dominos_pizza"
    item_attributes = {"brand": "Domino's", "brand_wikidata": "Q839466"}
    allowed_domains = ["dominos.com"]
    start_urls = ("https://pizza.dominos.com/sitemap.xml",)

    def parse_hours(self, hours):
        opening_hours = OpeningHours()
        for hour in hours:
            day = hour["dayOfWeek"].replace("http://schema.org/", "")
            opening_hours.add_range(
                day=DAY_MAPPING[day],
                open_time=hour["opens"],
                close_time=hour["closes"],
                time_format="%H:%M:%S",
            )

        return opening_hours.as_opening_hours()

    def parse_state_sitemap(self, response):
        xml = Selector(response)
        xml.remove_namespaces()

        urls = xml.xpath("//loc/text()").extract()
        urls = [url.strip() for url in urls]

        for url in urls:
            # store urls follow this pattern:
            # url must be 3 segments (state/city/address) and the last one cannot be a postalcode only or the words "chicken", "pasta", or "sandwiches".
            if re.match(r"^https://pizza.dominos.com/.*?/.*?/.*-.*?/$", url):
                yield scrapy.Request(url, callback=self.parse_place)

    def parse(self, response):
        xml = Selector(response)
        xml.remove_namespaces()

        urls = xml.xpath("//loc/text()").extract()
        urls = [url.strip() for url in urls]

        for url in urls:
            if "/home/" in url:
                continue
            yield scrapy.Request(url, callback=self.parse_state_sitemap)

    def parse_place(self, response):
        data = json.loads(response.xpath('//script[@type="application/ld+json"]/text()').extract_first())

        yield Feature(
            name=data["name"],
            lat=float(data["geo"]["latitude"]),
            lon=float(data["geo"]["longitude"]),
            phone=data.get("telephone"),
            website=response.url,
            ref=data["branchCode"],
            opening_hours=self.parse_hours(data["openingHoursSpecification"]),
            street_address=data["address"]["streetAddress"],
            city=data["address"]["addressLocality"],
            state=data["address"]["addressRegion"],
            postcode=data["address"]["postalCode"],
            country=data["address"]["addressCountry"],
        )
