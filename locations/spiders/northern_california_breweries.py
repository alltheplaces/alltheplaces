# -*- coding: utf-8 -*-
import scrapy
from locations.items import GeojsonPointItem
import json
import re

class NorthernCaliforniaBreweriesSpider(scrapy.Spider):
    name = "northern_california_breweries"
    allowed_domains = ["projects.sfchronicle.com"]
    start_urls = (
        'http://projects.sfchronicle.com/2017/brewery-map/',
    )

    def parse(self, response):
      beerData = response.xpath("//*[text()[contains(.,'beerData')]]").extract_first()
      matches = re.search(r"var beerData = (\[(.*)\])", beerData)
      jsonData = matches.group(0).replace("var beerData = ","")
      breweryList = json.loads(jsonData)

      for item in breweryList:
        yield GeojsonPointItem(
          ref=item.get('Brewery'),
          lat=float(item.get('Latitude')),
          lon=float(item.get('Longitude')),
          addr_full=item.get('Address'),
          city=item.get('City'),
          state="CA",
          website=item.get('Website'),
        )
