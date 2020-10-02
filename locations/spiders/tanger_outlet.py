# -*- coding: utf-8 -*-
import scrapy
from locations.items import GeojsonPointItem

class TangerOutletSpider(scrapy.Spider):
	name = "tanger_outlet"
	allowed_domains = ["www.tangeroutlet.com"]
	download_delay = 0.1
	start_urls = (
		"https://www.tangeroutlet.com/locations",
	)

	def parse(self, response):
		storeurls = response.xpath('.//a[@title="Visit"]/@href').extract()
		storeurls = [response.urljoin(i) for i in storeurls if 'location' in i]
		for storeurl in storeurls:
			yield scrapy.Request(storeurl, callback=self.parse_store)

	def parse_store(self, response):
		tempurl = '/' + response.url.split('/')[-2] + '/'
		for i in response.xpath('.//ul[@id="usCenters"]/li[@class="allCenters"]/a/@href').extract():
			if i == tempurl:
				latitude = float(response.xpath('.//ul[@id="usCenters"]/li[@class="allCenters"]/@data-longitude').extract_first())
				longitude = float(response.xpath('.//ul[@id="usCenters"]/li[@class="allCenters"]/@data-latitude').extract_first())
		try:
			properties = {
				'ref': response.url,
				'brand': 'Tanger Outlet',
				'addr_full': response.xpath('.//div[@class="centerLocation"]//span/text()').extract()[0],
				'city': response.xpath('.//div[@class="centerLocation"]//span/text()').extract()[1].split(',')[0],
				'state': response.xpath('.//div[@class="centerLocation"]//span/text()').extract()[1].split(',')[1].split()[0],
				'postcode': response.xpath('.//div[@class="centerLocation"]//span/text()').extract()[1].split(',')[1].split()[1],
				'phone': response.xpath('.//div[@class="centerLocation"]//span/text()').extract()[2],
				'lat': latitude,
				'lon': longitude,
				'website': response.url,
			}
			yield GeojsonPointItem(**properties)
		except:
			pass
		