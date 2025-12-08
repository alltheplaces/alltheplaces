import re

import scrapy

from locations.items import Feature


class BarnesAndNobleCollegeSpider(scrapy.Spider):
    name = "barnes_and_noble_college"
    item_attributes = {"brand": "Barnes & Noble College", "brand_wikidata": "Q4861508"}
    allowed_domains = ["bncollege.com"]
    start_urls = ("https://www.bncollege.com/campus-stores/",)

    def parse(self, response):
        locations = response.xpath('//section[@id="map-results"]//h3')
        address_data = response.xpath('//div[@class="address"]/p')

        for location, addresses, citypostal in zip(locations, address_data, address_data):
            name = location.xpath(".//text()").extract_first()
            address = addresses.xpath(".//text()").extract_first()
            city_postal = citypostal.xpath(".//text()").extract().pop(-1).strip()
            try:
                city_state, postal = re.search(r"\s+(.*)(\d{5})", city_postal).groups()
                city, state = city_state.split(",")
            except:
                continue

            properties = {
                "ref": name,
                "name": name,
                "street_address": address,
                "city": city.strip(),
                "state": state.strip(),
                "postcode": postal.strip(),
                "country": "US",
                "website": response.url,
            }

            yield Feature(**properties)
