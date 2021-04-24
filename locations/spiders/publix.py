# -*- coding: utf-8 -*-
import scrapy
import re

from locations.items import GeojsonPointItem


class PublixSpider(scrapy.Spider):
    name = "publix"
    item_attributes = { 'brand': "Publix", 'brand_wikidata': "Q672170" }
    allowed_domains = ['publix.com']
    start_urls = (
        'http://weeklyad.publix.com/Publix/Entry/Locations/',
    )

    def parse(self, response):
        response.selector.remove_namespaces()
        city_urls = response.xpath('//a[@class="stdLink action-tracking-nav"]/@href').extract()
#        regex = re.compile(r'Publix\/BrowseByListing\/ByAllCategories\/\?StoreID=\d+')
        for path in city_urls:
#            if re.search(regex,path):
            yield scrapy.Request(
                str("http://weeklyad.publix.com") + path.strip(),
                callback=self.parse_ad,
            )


    def parse_ad(self, response):
        response.selector.remove_namespaces()
        if response.xpath('//h3[@class="weeklyAdsLoc_text"]/span[@class="mainLocName"]').extract_first():
            storeNumber = response.xpath('//h3[@class="weeklyAdsLoc_text"]/span[@class="mainLocName"]').extract_first().split('#')[1].split(')')[0]
            yield scrapy.Request(
                str("http://www.publix.com/locations/") + storeNumber.strip(),
                callback=self.parse_store,
            )


    def parse_store(self, response):

        if "CLOSED" == response.xpath('//span[@class="store-status"]/text()').extract_first():
            storeHours = 'STORE CLOSED'

        else:
            storeHoursHTML = response.xpath('//div[@class="store-info-group"]').extract()[4]
            p = re.compile(r'<.*?>')
            storeHours = p.sub('', storeHoursHTML)
            storeHours = storeHours.replace('\t', '').replace('\r', '').replace('\n', '').replace('       ', ' ')
            storeHours = "".join(storeHours.strip())


        properties = {
        'name': response.xpath('//h1[@id="content_2_TitleTag"]/text()').extract_first().strip(),
        'ref': response.xpath('//div[@class="store-info-group"]/text()').extract_first().strip(),
        'addr_full': response.xpath('///div[@class="store-info-group"][2]/text()').extract_first().strip(),
        'city': response.xpath('///div[@class="store-info-group"][2]/text()').extract()[1].split(',')[0].strip(),
        'state': response.xpath('//div[@class="store-info-group"]/text()').extract()[2].split('\xa0')[0].split('\t')[-1].strip(),
        'postcode': response.xpath('///div[@class="store-info-group"][2]/text()').extract()[1].split(',')[1].split()[1].strip(),
        'phone': response.xpath('///div[@class="store-info-group"]/div[1]/text()').extract_first(),
        'website': response.request.url,
        'opening_hours': storeHours,
        'lat': response.xpath('///div[@class="store-info-group"][4]/a/@href').extract_first().split('//')[2].split(',')[0],
        'lon': response.xpath('///div[@class="store-info-group"][4]/a/@href').extract_first().split('//')[2].split(',')[1],
        }


        yield GeojsonPointItem(**properties)
