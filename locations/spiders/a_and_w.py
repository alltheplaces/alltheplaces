# -*- coding: utf-8 -*-
'''
This spider has an issue with getting 302s, but should be capable of scraping latitude and longitude once that issue has been fixed.  See lines 51-54.
'''
import scrapy
import json
import re
import urllib.parse

from locations.items import GeojsonPointItem

def arraycommentgetter(scripts):
	for thing in scripts:
		if "Array" in thing.extract():
			return thing.extract()

class AWSpider(scrapy.Spider):
	name = "a_and_w"
	allowed_domains = ["awrestaurants.com"]
	states = ["AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ", "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC", "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"]
	url = "https://awrestaurants.com/locations?zipcode="
	start_urls = ["https://awrestaurants.com/locations?zipcode=" + state for state in states]
	# for each restaurant there's a commented out PHP "Array" in a <script> on the restaurant page
	# we can get all restaurants by starting from all state search pages
	# for each state PAGE, make list of address URLs
	# for each address URL, open the restaurant PAGE
	# on each restaurant page, scrape the goodies

	def parse(self, response):
		addresses = response.xpath('//input[@id="zipcode"]/@value')[1:].extract()
		addresses = set(addresses)
		#need to clean addresses by removing all periods from strings! do this
		listofaddresses = []
		for address in addresses:
			listofaddresses.append("https://awrestaurants.com/changeloc.php?zipcode="+urllib.parse.quote(address))
		for address in listofaddresses:
			yield scrapy.Request(
				address,
				callback=self.parse_location,
				headers={'authority':'awrestaurants.com',
										'method':'GET',
										'scheme':'https',
										'accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
										'accept-encoding':'gzip, deflate, br',
										'accept-language':'en-US,en;q=0.9',
										'referer':'https://awrestaurants.com/locations?zipcode=AR',
										'upgrade-insecure-requests':'1',
										'cookie':'__cfduid=d2208e6804dac9b0f0a8d7fe0cfcbf6a31512839792; SSESS57889cb8eac34df8bd9c66cd80e5ae39=PhEfEGVloxHUOL4Cgj6685wAByghVxR-R1tcaJQaWn8; SSESS81733e72250eea6616f0d89a17f3e548=2UzuITQHZL7srIzk8lQhnSOzQr8Y40KTIPOx_iRTClI; _cb_ls=1; c_mlocation=true; multibrand_tid=10; c_mlat=37.138080; c_mlong=-85.972872; master_id=07079; user_loc=1; expires=1513877811000; has_js=1; location=1525; _ga=GA1.2.1048022298.1512839794; _gid=GA1.2.2135449082.1513787202; _cb=DYBnFhCa2xQ2BcFxeU; _chartbeat2=.1512840206273.1513886348108.1001000000011.CapsDkBHt2_PC1F2hj74q7SYzBKm; _cb_svref=null',
										'user-agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36'
										}
				# these headers don't actually fix our cookies/302 problem. see
				# https://doc.scrapy.org/en/latest/topics/downloader-middleware.html#std:reqmeta-cookiejar
				# or
				# https://doc.scrapy.org/en/latest/topics/practices.html#avoiding-getting-banned									
			)

	def parse_location(self, response):
		props = {}
		scripts = response.xpath('//script')
		lines = arraycommentgetter(scripts).split('\n')
		stripped = [x.strip() for x in lines]
		for line in stripped:
			if line.startswith("[city"):
				props['city'] = re.search('=> (.*)',line).group(1)
			if line.startswith("[state"):
				props['state'] = re.search('=> (.*)',line).group(1)
			if line.startswith("[zip"):
				props['postcode'] = re.search('=> (.*)',line).group(1)
			if line.startswith("[storelat"):
				props['lat'] = re.search('=> (.*)',line).group(1)
			if line.startswith("[storelon"):
				props['lon'] = re.search('=> (.*)',line).group(1)
			if line.startswith("[user_zip"):
				props['addr_full'] = re.search('=> (.*)',line).group(1)
			if line.startswith("[nid"):
				props['ref'] = re.search('=> (.*)',line).group(1)
			else:
				pass
		props['phone'] = response.xpath('//*[@id="fixedBox"]/section[1]/span[2]/text()').extract()
		props['country'] = "US"
		#print(props)
		yield GeojsonPointItem(**props)