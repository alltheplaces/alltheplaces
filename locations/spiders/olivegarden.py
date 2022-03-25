# -*- coding: utf-8 -*-
import json
import scrapy
import re

from locations.items import GeojsonPointItem


class OliveGardenSpider(scrapy.Spider):
    name = "olivegarden"
    item_attributes = {"brand": "Olive Garden", "brand_wikidata": "Q3045312"}
    allowed_domains = ["olivegarden.com"]
    download_delay = 0.5
    start_urls = ("http://www.olivegarden.com/en-locations-sitemap.xml",)

    def address(self, address):
        if not address:
            return None

        addr_tags = {
            "addr_full": address[0].split('value="')[1].split('"')[0].split(",")[0],
            "city": address[0].split('value="')[1].split('"')[0].split(",")[1],
            "state": address[0].split('value="')[1].split('"')[0].split(",")[-2],
            "postcode": address[0].split('value="')[1].split('"')[0].split(",")[-1],
        }

        return addr_tags

    def parse(self, response):
        response.selector.remove_namespaces()
        city_urls = response.xpath("//url/loc/text()").extract()
        locationURL = re.compile(r"http[s]:/(/|/www.)olivegarden.com/locations/\S+")
        for path in city_urls:
            if not re.search(locationURL, path):
                pass
            else:
                yield scrapy.Request(
                    path.strip(),
                    callback=self.parse_store,
                )

    def parse_store(self, response):
        if response.url == "https://www.olivegarden.com/home":
            return

        data = json.loads(
            response.xpath(
                '//script[@type="application/ld+json"]/text()'
            ).extract_first()
        )
        fallback = False

        try:
            properties = {
                "ref": response.url.split("/")[-1],
                "name": data["name"],
                "addr_full": data["address"].get("streetAddress", "").strip(),
                "city": data["address"]["addressLocality"],
                "state": data["address"]["addressRegion"],
                "postcode": data["address"]["postalCode"],
                "country": data["address"]["addressCountry"],
                "phone": data.get("telephone", None),
                "lat": float(data["geo"]["latitude"]),
                "lon": float(data["geo"]["longitude"]),
                "website": response.url,
            }

        except KeyError:  # a few location pages don't have the complete ld+json data
            properties = {}
            fallback = True

        if not properties.get("city", False) or fallback:
            properties = {
                "name": response.xpath(
                    'normalize-space(//input[@id="isLocationDetails"]/../h1/text())'
                ).extract_first(),
                "website": response.url,
                "ref": response.url.split("/")[-1],
                "country": "US",
                "lon": float(
                    response.xpath('//input[@id="restLatLong"]')
                    .extract_first()
                    .split('value="')[1]
                    .split('"')[0]
                    .split(",")[1]
                ),
                "lat": float(
                    response.xpath('//input[@id="restLatLong"]')
                    .extract_first()
                    .split('value="')[1]
                    .split('"')[0]
                    .split(",")[0]
                ),
            }

            address = self.address(
                response.xpath('//input[@id="restAddress"]').extract()
            )
            if address:
                properties.update(address)

        yield GeojsonPointItem(**properties)
