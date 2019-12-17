import scrapy
import re
from locations.items import GeojsonPointItem

class WegmansSpider(scrapy.Spider):

    name = "wegmans"
    brand = "Wegmans"
    allowed_domains = ["www.wegmans.com"]
    download_delay = 1.5
    start_urls = (
        'https://www.wegmans.com/stores.html',
    )
    def parse_stores(self, response):
        properties = {
            'addr_full': response.xpath('normalize-space(//meta[@name="address"]/@content)').extract_first(),
            'phone': response.xpath('normalize-space(//meta[@name="phone"]/@content)').extract_first(),
            'city': response.xpath('normalize-space(//meta[@name="city"]/@content)').extract_first(),
            'state': response.xpath('normalize-space(//meta[@name="stateAbbreviation"]/@content)').extract_first(),
            'postcode':response.xpath('normalize-space(//meta[@name="zip"]/@content)').extract_first(),
            'ref': response.xpath('normalize-space(//meta[@name="id"]/@content)').extract_first(),
            'website': response.url,
            'lat':  response.xpath('normalize-space(//input[@id="storeLocation"]/@data-lat)').extract_first(),
            'lon':  response.xpath('normalize-space(//input[@id="storeLocation"]/@data-long)').extract_first(),
        }
        
        yield GeojsonPointItem(**properties)
    def parse(self, response):
        urls = response.xpath('//div[@class="cta-rte"]/p/a/@href').extract()
        for path in urls:
                yield scrapy.Request(response.urljoin(path), callback=self.parse_stores)
