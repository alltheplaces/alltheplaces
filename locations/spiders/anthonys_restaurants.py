# -*- coding: utf-8 -*-
import scrapy
from locations.items import GeojsonPointItem


class AnthonysRestaurantsSpiders(scrapy.Spider):
    name = "anthonys_restaurants"
    item_attributes = { 'brand': "Anthony's" }
    allowed_domains = ["www.anthonys.com"]
    start_urls = (
        'https://www.anthonys.com/restaurants/search/47.6062095/-122.3320708/2000',
    )

    def parse(self, response):
        for match in response.xpath("//markers/marker"):
            fullAddress=match.xpath('.//@address').extract_first().replace('<br />', ',')

            # Accounts for cases with second address line
            if(len(fullAddress.split(",")) == 4):
                cityString = fullAddress.split(",")[2].strip()
                stateString = fullAddress.split(",")[3].strip().split(" ")[0].strip()
                postString = fullAddress.split(",")[3].strip().split(" ")[1].strip()
                addrLineOne = fullAddress.split(",")[0].strip()
                addrLineTwo = fullAddress.split(",")[1].strip()
                addrString = addrLineOne + ", " + addrLineTwo
            else:
                cityString = fullAddress.split(",")[1].strip()
                stateString = fullAddress.split(",")[2].strip().split(" ")[0].strip()
                postString = fullAddress.split(",")[2].strip().split(" ")[1].strip()
                addrString = fullAddress.split(",")[0]

            yield GeojsonPointItem(
                ref=match.xpath('.//@title').extract_first().strip(),
                lat=match.xpath('.//@lat').extract_first().strip(),
                lon=match.xpath('.//@lng').extract_first().strip(),
                addr_full=addrString,
                city=cityString,
                state=stateString,
                postcode=postString,
                phone=match.xpath('.//@phone').extract_first().replace(" ", ""),
            )
