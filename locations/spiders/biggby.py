# -*- coding: utf-8 -*-
import json
import scrapy
from xml.etree import ElementTree as ET
from scrapy import Selector

from locations.items import GeojsonPointItem


class BiggbySpider(scrapy.Spider):
    name = "biggby"
    allowed_domains = ["www.biggby.com"]
    start_urls = (
        'https://www.biggby.com/locations/',
    )

    def parse(self, response):
        # retrieve XML data from DIV tag
		items = response.xpath("//div[@id='loc-list']/markers").extract()
		
		# convert data variable from unicode to string
		items = [str(x) for x in items]

		# create element tree object
		root = ET.fromstring(items[0])

		# iterate items
		for child in root:
			# print child.attrib['name']
			yield GeojsonPointItem(
				ref=child.attrib['pid'],
				lat=float(child.attrib['lat']),
				lon=float(child.attrib['lng']),
				addr_full=child.attrib['address-two'],
				city=child.attrib['city'],
				state=child.attrib['state'],
				postcode=child.attrib['zip'],
				name=child.attrib['name'],
				# website='https://www.superonefoods.com/store-details/'+item.get('url'),
			)
