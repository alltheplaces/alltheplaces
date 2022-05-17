# -*- coding: utf-8 -*-
import json

import scrapy

from locations.items import GeojsonPointItem


class KaiserPermanenteSpider(scrapy.Spider):
    name = "kaiser_permanente"
    item_attributes = {"brand": "Kaiser Permanente", "brand_wikidata": "Q1721601"}
    allowed_domains = [
        "healthy.kaiserpermanente.org",
        "locations.kaiserpermanentejobs.org",
    ]
    start_urls = [
        "https://healthy.kaiserpermanente.org/northern-california/facilities/sitemap",
        "https://healthy.kaiserpermanente.org/southern-california/facilities/sitemap",
        "https://healthy.kaiserpermanente.org/colorado-denver-boulder-mountain-northern/facilities/sitemap",
        "https://healthy.kaiserpermanente.org/southern-colorado/facilities/sitemap",
        "https://healthy.kaiserpermanente.org/georgia/facilities/sitemap",
        "https://healthy.kaiserpermanente.org/hawaii/facilities/sitemap",
        "https://healthy.kaiserpermanente.org/maryland-virginia-washington-dc/facilities/sitemap",
        "https://healthy.kaiserpermanente.org/oregon-washington/facilities/sitemap",
    ]
    download_delay = 0.3

    def parse(self, response):
        response.selector.remove_namespaces()
        locations = response.xpath("//url/loc/text()").extract()

        for location in locations:
            yield scrapy.Request(location, callback=self.parse_location)

    def parse_location(self, response):
        data = json.loads(
            response.xpath(
                '//script[@type="application/json" and contains(text(), "address")]/text()'
            ).extract_first()
        )

        coords = data.get("position", "")  # Handle missing coordinates
        lat = float(data["position"]["lat"]) if coords else None
        lon = float(data["position"]["lng"]) if coords else None

        properties = {
            "name": data["name"],
            "ref": data["id"],
            "addr_full": data["address"]["street"],
            "city": data["address"]["city"],
            "state": data["address"]["state"],
            "postcode": data["address"]["zip"],
            "phone": response.xpath(
                'normalize-space(//div[@class="fb__phone-number styling-5-marketing"]/text())'
            ).extract_first(),
            "website": data.get("homeUrl") or response.url,
            "lat": lat,
            "lon": lon,
        }

        yield GeojsonPointItem(**properties)
