import html
import json
import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class BMOHarrisSpider(scrapy.Spider):
    name = "bmo-harris"
    chain_name = "BMO Harris Bank"
    allowed_domains = ["branches.bmoharris.com"]
    download_delay = 0.5
    start_urls = (
        'https://branches.bmoharris.com/',
    )

    def parse_store(self, response):
        properties = {
            'addr_full': response.xpath('//meta[@property="business:contact_data:street_address"]/@content').extract_first(),
            'phone': response.xpath('//meta[@property="business:contact_data:phone_number"]/@content').extract_first(),
            'city': response.xpath('//meta[@property="business:contact_data:locality"]/@content').extract_first(),
            'state': response.xpath('//meta[@property="business:contact_data:region"]/@content').extract_first(),
            'postcode': response.xpath('//meta[@property="business:contact_data:postal_code"]/@content').extract_first(),
            'country': response.xpath('//meta[@property="business:contact_data:country_name"]/@content').extract_first(),
            'ref': response.url,
            'website': response.url,
            'lat': response.xpath('//meta[@property="place:location:latitude"]/@content').extract_first(),
            'lon': response.xpath('//meta[@property="place:location:longitude"]/@content').extract_first(),
        }

        yield GeojsonPointItem(**properties)

    def parse(self, response):
        # Step into hierarchy of place
        for url in response.xpath("//div[@class='itemlist']/p/a/@href").extract():
            yield scrapy.Request(response.urljoin(url))

        # Look for links to stores
        for url in response.xpath("//div[@class='itemlist']/li/span[@itemprop='streetAddress']/a/@href").extract():
            yield scrapy.Request(response.urljoin(url), callback=self.parse_store)
