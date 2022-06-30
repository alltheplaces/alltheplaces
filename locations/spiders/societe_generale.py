# -*- coding: utf-8 -*-
import json
import xmltodict

import scrapy

from locations.items import GeojsonPointItem


class SocieteGeneraleSpider(scrapy.Spider):
    name = "societe_generale"
    item_attributes = {"brand": "Societe Generale", "brand_wikidata": "Q270363"}
    allowed_domains = ["societegenerale.com", "agences.societegenerale.fr"]
    start_urls = [
        "https://agences.societegenerale.fr/banque-assurance/sitemap_agence_pois.xml",
    ]

    def parse(self, response):
        data = xmltodict.parse(response.text)
        for url in data["urlset"]["url"]:
            if "loc" in url:
                yield scrapy.Request(url=url["loc"], callback=self.parse_store)

    def parse_store(self, response):
        # Get all script tags with type application/ld+json
        store = json.loads(
            response.xpath('//script[@type="application/ld+json"]/text()').get()
        )
        address = store.get("address")
        oh = {}
        for d in store["openingHoursSpecification"]:
            day = d.get("dayOfWeek")[18:20]
            op = d.get("opens")
            cl = d.get("closes")
            if day not in oh:
                oh[day] = f"{op} - {cl}"
            else:
                oh[day] += f" | {op} - {cl}"

        string_oh = ""
        for k, v in oh.items():
            string_oh += f"{k}: {v}, "
        properties = {
            "lat": store["geo"]["latitude"],
            "lon": store["geo"]["longitude"],
            "name": store["name"],
            "street_address": address.get("streetAddress"),
            "city": store["address"].get("city"),
            "postcode": address.get("postalCode"),
            "country": address.get("addressCountry"),
            "website": response.url,
            "ref": store["name"],
            "opening_hours": string_oh,
        }

        yield GeojsonPointItem(**properties)
