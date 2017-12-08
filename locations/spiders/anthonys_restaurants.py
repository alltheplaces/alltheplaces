# -*- coding: utf-8 -*-
import scrapy
from locations.items import GeojsonPointItem
import json
import re

class AnthonysRestaurantsSpiders(scrapy.Spider):
    name = "anthonys_restaurants"
    allowed_domains = ["www.anthonys.com"]
    start_urls = (
        'https://www.anthonys.com/restaurants/search/47.6062095/-122.3320708/2000',
    )

    def parse(self, response):
        restaurantData = response.xpath("//markers").extract_first()
        matches = re.finditer("<marker [\S\s]+?\"\/>", restaurantData)




        for match in matches:
            matchString = match.group(0)
            fullAddress=re.findall("address=\"(.*?)\"", matchString)[0].replace('&lt;br /&gt;', ',')
            #Accounts for cases with second address line
            if(len(fullAddress.split(",")) == 3):
                cityString = fullAddress.split(",")[1].strip()
                stateString = fullAddress.split(",")[2].strip().split(" ")[0].strip()
                postString = fullAddress.split(",")[2].strip().split(" ")[1].strip()

            if(len(fullAddress.split(",")) == 4):
                cityString = fullAddress.split(",")[2].strip()
                stateString = fullAddress.split(",")[3].strip().split(" ")[0].strip()
                postString = fullAddress.split(",")[3].strip().split(" ")[1].strip()
            

            yield GeojsonPointItem(
              ref=re.findall("title=\"(.*?)\"", matchString)[0].strip(),
              lat=re.findall("lat=\"(.*?)\"", matchString)[0].strip(),
              lon=re.findall("lng=\"(.*?)\"", matchString)[0].strip(),
              addr_full=re.findall("address=\"(.*?)\"", matchString)[0].replace('&lt;br /&gt;', ',').strip(),
              city=cityString,
              state=stateString,
              postcode=postString,
              phone=re.findall("phone=\"(.*?)\"", matchString)[0].replace(' ','').strip(),
            )
