# -*- coding: utf-8 -*-
import json
import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class SpecsaversSpider(scrapy.spiders.SitemapSpider):
    download_delay = 5
    name = "specsavers"
    item_attributes = {"brand": "Specsavers", "brand_wikidata": "Q2000610"}
    allowed_domains = ["specsavers.co.uk"]
    sitemap_urls = ["https://www.specsavers.co.uk/sitemap.xml"]
    sitemap_rules = [
        (
            "https:\/\/www\.specsavers\.co\.uk\/stores\/([\w-]+)",
            "parse_store",
        ),
    ]

    def sitemap_filter(self, entries):
        for entry in entries:
            if entry["loc"] != "https://www.specsavers.co.uk/stores/highlands":
                yield entry

    def parse_store(self, response):
        jsonld = response.xpath('//script[@type="application/ld+json"]/text()').get()
        ld = json.loads(jsonld)

        properties = {
            "phone": ld["telephone"],
            "street_address": ld["address"]["streetAddress"],
            "city": ld["address"]["addressLocality"],
            "postcode": ld["address"]["postalCode"],
            "country": ld["address"]["addressCountry"],
            "ref": ld["@id"],
            "website": ld["url"],
            "lat": ld["geo"]["latitude"],
            "lon": ld["geo"]["longitude"],
            "name": ld["name"],
        }

        oh = OpeningHours()
        for rule in ld["openingHoursSpecification"]:
            for day in rule["dayOfWeek"]:
                oh.add_range(day[:2], rule["opens"], rule["closes"])

        properties["opening_hours"] = oh.as_opening_hours()

        yield GeojsonPointItem(**properties)
