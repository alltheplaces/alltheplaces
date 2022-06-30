# -*- coding: utf-8 -*-

import scrapy

from locations.items import GeojsonPointItem


class SocieteGeneraleSpider(scrapy.Spider):
    name = "societe_generale"
    item_attributes = {"brand": "Societe Generale", "brand_wikidata": "Q270363"}
    allowed_domains = ["societegenerale.com"]
    start_urls = [
        "https://www.societegenerale.com/en/about-us/our-businesses/our-locations",
    ]

    def parse(self, response):
        template = "https://www.societegenerale.com/implentation/map-filter?lang=en-soge&country={country}&job=allmet&entity=allent"

        countries = response.xpath(
            '//select[@id="country"]/optgroup/option/text()'
        ).extract()

        for country in countries:
            if country == "All countries":
                pass
            else:
                url = template.format(country=country)
                yield scrapy.Request(url, callback=self.parse_location)

    def parse_location(self, response):
        data = response.json()
        stores = data["markers"]["places"]
        for store in stores:
            properties = {
                "ref": "{}_{}".format(
                    store["name"].lower().replace(" ", "_"), store["id"]
                ),
                "name": store["name"],
                "addr_full": store["address"],
                "city": store["city"],
                "country": store["country"],
                "phone": store["phone"],
                "lat": float(store["latitude"]),
                "lon": float(store["longitude"]),
                "website": store.get("url"),
            }

            yield GeojsonPointItem(**properties)
