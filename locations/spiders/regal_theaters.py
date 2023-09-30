import json
import re

import scrapy

from locations.items import Feature


class RegalTheatersSpider(scrapy.Spider):
    name = "regal_theaters"
    item_attributes = {"brand": "Regal Theaters"}
    allowed_domains = ["www.regmovies.com"]
    start_urls = ["https://www.regmovies.com/theatres/regal-riviera/0690"]
    requires_proxy = "US"

    def parse(self, response):
        data = response.xpath('//script[contains(., "apiSitesList")]').extract_first()

        theater_data = re.search(r"apiSitesList\s=\s(.*),", data).groups()[0]

        theaters = json.loads(theater_data)
        for theater in theaters:
            properties = {
                "ref": theater["externalCode"],
                "name": theater["name"],
                "street_address": theater["address"]["address1"],
                "city": theater["address"]["city"],
                "state": theater["address"]["state"],
                "postcode": theater["address"]["postalCode"],
                "country": "US",
                "lat": theater["latitude"],
                "lon": theater["longitude"],
                "website": "https://www.regmovies.com" + theater["uri"],
            }

            yield Feature(**properties)
