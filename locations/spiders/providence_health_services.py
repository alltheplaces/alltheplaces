# -*- coding: utf-8 -*-
import json

from scrapy.spiders import SitemapSpider
from locations.items import GeojsonPointItem


class ProvidenceHealthServicesSpider(SitemapSpider):
    name = "providence_health_services"
    item_attributes = {
        "brand": "Providence Health Services",
        "brand_wikidata": "Q7252430",
    }
    allowed_domains = ["providence.org"]
    download_delay = 0.2
    sitemap_urls = ["https://www.providence.org/sitemap.xml"]
    sitemap_rules = [
        (
            "https:\/\/www\.providence\.org\/locations\/[-\w]+$",
            "parse_location",
        )
    ]

    def parse_location(self, response):
        ldjson = json.loads(
            response.css('script[type="application/ld+json"]::text').get()
        )
        lat = ldjson["geo"]["latitude"]
        lon = ldjson["geo"]["longitude"]
        if (lat, lon) == (0, 0):
            return
        properties = {
            "lat": lat,
            "lon": lon,
            "ref": response.url,
            "phone": ldjson["telephone"],
            "name": ldjson["name"],
            "website": response.url,
        }
        if "address" in ldjson:
            address = ldjson["address"]
            properties.update(
                {
                    "addr_full": address["streetAddress"],
                    "city": address["addressLocality"],
                    "state": address["addressRegion"],
                    "postcode": address["postalCode"],
                }
            )
        yield GeojsonPointItem(**properties)
