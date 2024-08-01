import json
import re

import scrapy
from scrapy.selector import Selector

from locations.hours import OpeningHours
from locations.items import Feature

DAY_MAPPING = {
    "Monday": "Mo",
    "Tuesday": "Tu",
    "Wednesday": "We",
    "Thursday": "Th",
    "Friday": "Fr",
    "Saturday": "Sa",
    "Sunday": "Su",
}


class RentacenterSpider(scrapy.Spider):
    name = "rentacenter"
    item_attributes = {"brand": "Rent-A-Center", "brand_wikidata": "Q7313497"}
    allowed_domains = ["rentacenter.com"]

    start_urls = [
        "https://locations.rentacenter.com/sitemap.xml",
    ]

    def parse_hours(self, hours):
        opening_hours = OpeningHours()

        for hour in hours:
            opening_hours.add_range(
                day=DAY_MAPPING[hour["dayOfWeek"].replace("http://schema.org/", "")],
                open_time=hour["opens"],
                close_time=hour["closes"],
                time_format="%H:%M:%S",
            )

        return opening_hours.as_opening_hours()

    def parse_location(self, response):
        data = response.xpath('//script[@type="application/ld+json"]/text()').extract_first()
        data = json.loads(data)

        ref = data.get("branchCode")
        if not ref:
            return  # not a store page

        properties = {
            "street_address": data["address"]["streetAddress"],
            "phone": data.get("telephone"),
            "city": data["address"]["addressLocality"],
            "state": data["address"]["addressRegion"],
            "postcode": data["address"]["postalCode"],
            "country": "US",
            "ref": ref,
            "website": response.url,
            "lat": data["geo"]["latitude"],
            "lon": data["geo"]["longitude"],
            "name": data["name"],
        }

        hours = self.parse_hours(data.get("openingHoursSpecification", []))
        if hours:
            properties["opening_hours"] = hours

        yield Feature(**properties)

    def parse_state_sitemap(self, response):
        xml = Selector(response)
        xml.remove_namespaces()

        urls = xml.xpath("//loc/text()").extract()
        urls = [url.strip() for url in urls]

        # individual store pages are listed at top, then a state page, then bunch of other non-store pages
        # find the index position of the state page and then only parse urls before that
        i = urls.index(re.search(r"^(https://locations.rentacenter.com/.+?)/.*$", urls[0]).groups()[0] + "/")
        for url in urls[:i]:
            yield scrapy.Request(url, callback=self.parse_location)

    def parse(self, response):
        xml = Selector(response)
        xml.remove_namespaces()

        urls = xml.xpath("//loc/text()").extract()
        urls = [url.strip() for url in urls]

        for url in urls:
            if "/home/" in url:
                continue
            yield scrapy.Request(url, callback=self.parse_state_sitemap)
