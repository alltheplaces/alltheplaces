# -*- coding: utf-8 -*-
import json
import re
import scrapy
from locations.items import GeojsonPointItem

COUNTRIES = {"Canada": "CA", "Turkey": "TR", "United States": "US", "Mexico": "MX", "Honduras": "HN", "Chile": "CL", "Colombia": "CO"}

class LaQuintaSpider(scrapy.Spider):
    name = "la_quinta"
    allowed_domains = ["www.wyndhamhotels.com"]
    start_urls = (
        'https://www.wyndhamhotels.com/laquinta/locations',
    )

    def parse(self, response):
        hotels = [response.urljoin(l) for l in response.xpath("//a/@href").getall() if l.endswith("overview")]
        for idx, hotel in enumerate(hotels):
            yield scrapy.Request(hotel, callback=self.parse_property,meta={"id": idx})

    def parse_property(self, response):
        raw_json = re.search("<script type=\"application\/ld\+json\"\>(.+?)\<", response.text, flags=re.DOTALL).group(1)
        data = json.loads(raw_json)
        properties = {
            "ref": response.meta["id"],
            "lat": data["geo"]["latitude"],
            "lon": data["geo"]["longitude"],
            "name": data["name"],
            "addr_full": data["address"]["streetAddress"],
            "city": data["address"]["addressLocality"],
            "state": data["address"].get("addressRegion"),
            "postcode": data["address"]["postalCode"],
            "country": COUNTRIES[data["address"]["addressCountry"]],
            "phone": data["telephone"],
            "website": response.url,
            "brand": "La Quinta",
        }
        yield GeojsonPointItem(**properties)

        