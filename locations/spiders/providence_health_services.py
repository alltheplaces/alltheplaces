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

    def sitemap_filter(self, entries):
        for entry in entries:
            # sitemap now includes language codes, but are always redirected to the base url
            entry["loc"] = entry["loc"].replace(
                "https://www.providence.org/en/", "https://www.providence.org/"
            )
            # skip bad page
            if (
                entry["loc"]
                == "https://www.providence.org/locations/saint-johns-santa-monica-pediatrics-1811-wilshire"
            ):
                continue

            yield entry

    def parse_location(self, response):
        ldjson = json.loads(
            response.css('script[type="application/ld+json"]::text').get()
        )

        if ldjson["@type"] == "SpecialAnnouncement":
            ldjson = ldjson["announcementLocation"]

        lat = ldjson["geo"]["latitude"]
        lon = ldjson["geo"]["longitude"]
        if (lat, lon) == (0, 0):
            return
        properties = {
            "lat": lat,
            "lon": lon,
            "ref": response.url,
            "phone": ldjson.get("telephone"),
            "name": ldjson["name"],
            "website": response.url,
        }
        if "address" in ldjson:
            address = ldjson["address"]
            properties.update(
                {
                    "street_address": address["streetAddress"],
                    "city": address["addressLocality"],
                    "state": address["addressRegion"],
                    "postcode": address["postalCode"],
                }
            )
        yield GeojsonPointItem(**properties)
