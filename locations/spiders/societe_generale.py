# -*- coding: utf-8 -*-
import json

from scrapy.spiders import SitemapSpider

from locations.hours import OpeningHours
from locations.items import GeojsonPointItem


class SocieteGeneraleSpider(SitemapSpider):
    name = "societe_generale"
    item_attributes = {"brand": "Societe Generale", "brand_wikidata": "Q270363"}
    allowed_domains = ["societegenerale.com", "agences.societegenerale.fr"]
    sitemap_urls = [
        "https://agences.societegenerale.fr/banque-assurance/sitemap_agence_pois.xml",
    ]

    def parse(self, response):
        # Get all script tags with type application/ld+json
        store = json.loads(
            response.xpath('//script[@type="application/ld+json"]/text()').get()
        )
        address = store.get("address")
        oh = OpeningHours()
        for d in store["openingHoursSpecification"]:
            day = d.get("dayOfWeek")[18:20]
            op = d.get("opens")
            cl = d.get("closes")

            oh.add_range(day, op, cl)

        properties = {
            "lat": store["geo"]["latitude"],
            "lon": store["geo"]["longitude"],
            "name": store["name"],
            "street_address": address.get("streetAddress"),
            "city": store["address"].get("city"),
            "postcode": address.get("postalCode"),
            "country": address.get("addressCountry"),
            "website": response.url,
            "ref": store["@id"],
            "opening_hours": oh.as_opening_hours(),
            "phone": store.get("telephone").replace(".", " "),
        }

        yield GeojsonPointItem(**properties)
