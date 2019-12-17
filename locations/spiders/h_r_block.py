import scrapy
import re
from locations.items import GeojsonPointItem

DAY_MAPPING = {
    'M': 'Mo',
    'T': 'Tu',
    'W': 'We',
    'F': 'Fr',
    'Sat': 'Sa',
    'Sun': 'Su'
}


class HRBlockSpider(scrapy.Spider):

    name = "h_r_block"
    chain_name = "H & R Block"
    allowed_domains = ["www.hrblock.com"]
    download_delay = 0.5
    start_urls = (
        'https://www.hrblock.com/tax-offices/local/',
    )

    def parse_stores(self, response):
        ref =  re.findall(r"[0-9]+$" , response.url)
        if(len(ref)>0):
            ref = ref[0]
        else:
            ref = response.url
        properties = {
            'addr_full' : ' '.join(response.xpath('//span[@itemprop="streetAddress"]/text()').extract()),
            'phone' : response.xpath('normalize-space(//span[@itemprop="telephone"]/text())').extract_first(),
            'city' : response.xpath('normalize-space(//span[@itemprop="addressLocality"]/text())').extract_first(),
            'state' : response.xpath('normalize-space(//span[@itemprop="addressRegion"]/text())').extract_first(),
            'postcode' : response.xpath('normalize-space(//span[@itemprop="postalCode"]/text())').extract_first(),
            'ref' : ref,
            'website' : response.xpath('//link[@rel="canonical"]/@href').extract_first(),
            'lat' : float(response.xpath('normalize-space(//meta[@itemprop="latitude"]/@content)').extract_first()),
            'lon' : float(response.xpath('normalize-space(//meta[@itemprop="longitude"]/@content)').extract_first()),
        }
        yield GeojsonPointItem(**properties)

    def parse_city_stores(self, response):
        stores = response.xpath('//div[@itemtype="https://schema.org/LocalBusiness"]/div/div/a/@href').extract()
        for store in stores:
            if store:
                yield scrapy.Request(response.urljoin(store), callback=self.parse_stores)

    def parse_state(self, response):

        city_urls = response.xpath('//div[@class="cities-list clearfix"]/a/@href').extract()
        for path in city_urls:
            yield scrapy.Request(response.urljoin(path), callback=self.parse_city_stores)

    def parse(self, response):
        urls = response.xpath('//div[@class="ol-states clearfix"]/a/@href').extract()
        for path in urls:
            yield scrapy.Request(response.urljoin(path), callback=self.parse_state)
