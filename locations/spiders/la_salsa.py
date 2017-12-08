# -*- coding: utf-8 -*-
import scrapy
from locations.items import GeojsonPointItem
import json
import re

class LaSalsaSpider(scrapy.Spider):
    name = "la_salsa"
    allowed_domains = ["www.lasalsa.com"]
    start_urls = (
        'http://lasalsa.com/wp-content/themes/lasalsa-main/locations-search.php?lat=0&lng=0&radius=99999999',
    )

    def parse(self, response):
        restaurantData = response.xpath("//markers").extract_first()
        matches = re.finditer("<marker [\S\s]+?\"\/>", restaurantData)




        for match in matches:
            matchString = match.group(0)
            fullAddress=re.findall("address=\"(.*?)\"", matchString)[0].replace('&lt;br /&gt;', ',')
            #Accounts for cases with second address line

            yield GeojsonPointItem(
              ref=re.findall("name=\"(.*?)\"", matchString)[0].strip(),
              lat=re.findall("latitude=\"(.*?)\"", matchString)[0].strip(),
              lon=re.findall("longitude=\"(.*?)\"", matchString)[0].strip(),
              addr_full=re.findall("address=\"(.*?)\"", matchString)[0].replace('&lt;br /&gt;', ',').strip(),
              city=re.findall("city=\"(.*?)\"", matchString)[0].strip(),
              state=re.findall("state=\"(.*?)\"", matchString)[0].strip(),
              postcode=re.findall("zip=\"(.*?)\"", matchString)[0].strip(),
              phone=re.findall("phone=\"(.*?)\"", matchString)[0].replace(' ','').strip(),
            )
            