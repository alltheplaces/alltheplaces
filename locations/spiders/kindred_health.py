# -*- coding: utf-8 -*-
import scrapy
import json
import re
from scrapy.spiders import SitemapSpider
from locations.items import GeojsonPointItem


class KindredHealthSpider(SitemapSpider):
    name = "kindred_health"
    item_attributes = {'brand': "Kindred Health Care" }
    allowed_domains = ["kindredhealthcare.com"]

    sitemap_urls = [
        "https://www.kindredhealthcare.com/sitemap/sitemap.xml",
    ]
    sitemap_rules = [
        ('/locations/', 'parse_locations')
    ]

    def parse_locations(self, response):
        try:
            ref = re.search(r'.+/(.+?)/?(?:\.html|$)', response.url).group(1)
            data = json.loads(response.xpath('//input[@class="addressValueInput"]/@value').extract_first())

            properties = {
                'ref': ref.strip('/'),
                'addr_full': data['Street'],
                'city': data['City'],
                'state': data['StateCode'],
                'postcode': data['Zip'],
                'country': data['CountryCode'],
                'lat': float(data['Latitude']),
                'lon': float(data['Longitude']),
                'website': response.url
            }
            yield GeojsonPointItem(**properties)
        except:
            pass