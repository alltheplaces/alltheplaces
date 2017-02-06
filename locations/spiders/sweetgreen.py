# -*- coding: utf-8 -*-
import scrapy
import json
from scrapy.utils.url import urljoin_rfc
from scrapy.utils.response import get_base_url

from locations.items import GeojsonPointItem

class SweetgreenSpider(scrapy.Spider):
    name = "sweetgreen"
    allowed_domains = ["www.sweetgreen.com"]
    start_urls = (
        'http://www.sweetgreen.com/locations/',
    )

    def parse(self, response):
        location_hrefs = response.xpath('//a[contains(@class, "location")]')
        for location_href in location_hrefs:
            properties = {
                'name': location_href.xpath('@title')[0].extract(),
                'addr:full': location_href.xpath('@data-street')[0].extract(),
                'phone': location_href.xpath('@data-phone')[0].extract(),
                'ref': location_href.xpath('@id')[0].extract(),
            }

            lon_lat = [
                float(location_href.xpath('@data-longitude')[0].extract()),
                float(location_href.xpath('@data-latitude')[0].extract()),
            ]

            yield GeojsonPointItem(
                properties=properties,
                lon_lat=lon_lat,
            )
