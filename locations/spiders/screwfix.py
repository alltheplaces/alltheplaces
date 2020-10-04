# -*- coding: utf-8 -*-
import scrapy
from locations.items import GeojsonPointItem

class ScrewfixSpider(scrapy.Spider):
	name = "screwfix"
	allowed_domains = ["www.screwfix.com"]
	download_delay = 0.1
	start_urls = (
		"https://www.screwfix.com/jsp/tradeCounter/tradeCounterAllStoresPage.jsp",
	)

	def parse(self, response):
		storeurls = response.xpath(".//ul[@class='store-name']//a/@href").extract()
		storeurls = [response.urljoin(i) for i in storeurls]
		for i in range(len(storeurls)):
			yield scrapy.Request(storeurls[i], callback=self.parse_location)
	
	def parse_location(self, response):
		ref = response.url
		addr = [i.strip() for i in response.xpath(".//address/text()").extract()]
		addr = ', '.join(i for i in addr)
		print(addr)
		properties = {
			'brand': 'Screwfix',
			'ref': ref,
			'name': response.xpath(".//span[@class='tcName']/text()").extract_first(),
			'addr_full': addr,
			'opening_hours': str('; ' .join([i.strip() for i in response.xpath(".//dl/dd/text()").extract()])),
			'lat': float(response.xpath(".//input[@id='lat']/@value").extract_first()),
			'lon': float(response.xpath(".//input[@id='lng']/@value").extract_first()),
			'website': ref
		}
		yield GeojsonPointItem(**properties)