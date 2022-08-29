# -*- coding: utf-8 -*-
import json
import re

import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class ExtendedStayAmericaSpider(scrapy.Spider):
    name = "extended_stay_america"
    item_attributes = {
        "brand": "Extended Stay America",
        "brand_wikidata": "Q5421850",
        "country": "US",
    }
    allowed_domains = ["extendedstayamerica.com"]
    start_urls = [
        "https://www.extendedstayamerica.com/hotels/",
    ]
    user_agent="Mozilla/5.0 (iPad; CPU OS 12_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148"

    def parse(self, response):
        urls = response.xpath('//ul[@class="esa-locations-markets-list"]/li/a/@href').extract()
        for url in urls:
            yield scrapy.Request(response.urljoin(url), callback=self.parse_hotel_list)

    def parse_hotel_list(self, response):
        script = response.xpath("//script[contains(text(), 'hotelsData')]/text()").extract_first()
        hotels = json.loads(script[58:-3])

        for hotel in hotels:
            properties = {
                "name": hotel["title"],
                "ref": hotel["siteId"],
                "street_address": hotel["address"]["street"],
                "city": hotel["address"]["city"],
                "state": hotel["address"]["region"],
                "postcode": hotel["address"]["postalCode"],
                "website": response.urljoin(hotel["urlMap"]),
                "photo": response.urljoin(hotel["featuredImages"][0]["url"]),
                "phone": hotel["phone"],
                "lat": hotel["latitude"],
                "lon": hotel["longitude"],
            }

            yield GeojsonPointItem(**properties)
