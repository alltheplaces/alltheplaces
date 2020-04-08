# -*- coding: utf-8 -*-
import json
import scrapy

from locations.hours import OpeningHours
from locations.items import GeojsonPointItem
from scrapy.selector import Selector


default_headers = {
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_1) AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/63.0.3239.84 Safari/537.36"}


class KrogerSpider(scrapy.Spider):
    name = "kroger"
    item_attributes = { 'brand': "Kroger", 'brand_wikidata': "Q153417" }
    allowed_domains = ["www.kroger.com"]
    download_delay = 0.2

    def start_requests(self):
        urls = [
	    'https://www.kroger.com/storelocator-sitemap.xml',
        ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse, headers=default_headers)


    def parse(self, response):
        xml = Selector(response)
        xml.remove_namespaces()

        urls = xml.xpath('//loc/text()').extract()
        for url in urls:
            yield scrapy.Request(url, callback=self.parse_store, headers=default_headers)

    def parse_hours(self, hours):
        opening_hours = OpeningHours()

        for hour in hours:
            try:
                opening_hours.add_range(day=hour["dayOfWeek"].replace("http://schema.org/", "")[:2],
                                        open_time=hour["opens"],
                                        close_time=hour["closes"],
                                        time_format="%H:%M:%S")
            except:
                continue  # closed or no time range given

    def parse_store(self, response):
        data = response.xpath('//script[@type="application/ld+json"]/text()').extract_first()
        if data:
            data = json.loads(data)
        else:
            return

        properties = {
            'ref': response.url,
            'name': "%s Kroger" % data["name"],
            'addr_full': data["address"]["streetAddress"].strip(),
            'city': data["address"]["addressLocality"].strip(),
            'state': data["address"]["addressRegion"],
            'postcode': data["address"]["postalCode"],
            'country': data["address"].get("addressCountry"),
            'phone': data.get("telephone"),
            'lat': float(data["geo"]["latitude"]),
            'lon': float(data["geo"]["longitude"]),
            'website': data.get("url") or response.url,
        }

        hours = self.parse_hours(data['openingHoursSpecification'])
        if hours:
            properties["opening_hours"] = hours

        yield GeojsonPointItem(**properties)
