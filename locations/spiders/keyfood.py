# -*- coding: utf-8 -*-
import scrapy
import re
from locations.items import GeojsonPointItem
from scrapy.selector import Selector

import random

class KeyfoodSpider(scrapy.Spider):
	name = "keyfood"
	allowed_domains = ["keyfood.mywebgrocer.com"]
	start_urls = (
		'http://keyfood.mywebgrocer.com/StoreLocator.aspx',
	)

	def parse(self, response):

		# works ok for now, but should probably just populate with actual contents of dropdown, in case they add new states.
		states = ['CT','NJ','NY','PA']

		for state in states:

			yield scrapy.FormRequest.from_response(response=response,
											formdata={'postBack':'1', 'action':'GL', 'stateSelIndex':'', 'citySelIndex':'', 'selStates':state, 'selCities':'', 'txtZipCode':'', 'selZipCodeRadius':'5' },
											clickdata={'class': 'submitButton'},
											dont_filter=True,
											callback=self.parse_state)
	
	def parse_state(self,response):
		sel = Selector(response)
		stores = sel.css('div.StoreBox')

		for store in stores:



			name = store.css('.StoreTitle').xpath("text()").extract()
			address = store.css('.StoreAddress p').xpath("text()").extract()
			address1 = address[0]
			address2 = address[len(address)-1].split(',')
			store_hours = store.css('.StoreHours p.tInfo').xpath("text()").extract()
			phone = store.css('.StoreContact p.tInfo').xpath("text()").extract()

			properties = {
				'name': ''.join(name),
				'ref': ''.join(name).replace('(', '').replace(')', '').replace(' ', '_'),
				'street': address1,
				'city': address2[0],
				'state': address2[1].split(' ')[1],
				'postcode': address2[1].split(' ')[2],
				'opening_hours': store_hours,
				'phone': ''.join(phone)[7:]
			}

			# print(random.randint(1,1000000))

			yield GeojsonPointItem(**properties)