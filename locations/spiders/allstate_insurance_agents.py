import scrapy
import re
from locations.items import GeojsonPointItem

class AllstateInsurnceAgentsSpider(scrapy.Spider):

    name = "allstate_insurance_agents"
    brand = "Allstate Insurance Agents"
    allowed_domains = ["agents.allstate.com"]
    download_delay = 0.5
    start_urls = (
        'https://agents.allstate.com/',
    )

    def parse_stores(self, response):
        properties = {
            'addr_full': response.xpath('normalize-space(//span[@class="c-address-street c-address-street-1"]/text())').extract_first()+' '+response.xpath('normalize-space(//span[@class="c-address-street c-address-street-2"]/text())').extract_first(),
            'phone' : response.xpath('normalize-space(//span[@class="c-phone-number-text-number"]/text())').extract_first(),
            'city' : response.xpath('normalize-space(//span[@class="c-address-city"]/span/text())').extract_first(),
            'state' : response.xpath('normalize-space(//span[@class="c-address-state"]/text())').extract_first(),
            'postcode' : response.xpath('normalize-space(//span[@class="c-address-postal-code"]/text())').extract_first(),
            'ref' : re.findall('[^\/]+$' , response.url)[0].split('.')[0],
            'website' : response.xpath('//link[@rel="canonical"]/@href').extract_first(),
            'lat' : float(response.xpath('normalize-space(//meta[@name="geo.position"]/@content)').extract_first().split(';')[0]),
            'lon' :float(response.xpath('normalize-space(//meta[@name="geo.position"]/@content)').extract_first().split(';')[1])
        }
        hours = response.xpath('//meta[@itemprop="openingHours"]/@content').extract()
        content_hours = " ;".join(hours)
        if content_hours:
            properties['opening_hours'] = content_hours
        yield GeojsonPointItem(**properties)

    def parse_city_stores(self, response):
        stores = response.xpath('//h3[@class="agent-name"]/a[@class="agent-name-link"]/@href').extract()
        for store in stores:
                yield scrapy.Request(response.urljoin(store), callback=self.parse_stores)

    def parse_state(self, response):
        city_urls = response.xpath('//div[@class="row c-directory-list-content-wrapper"]/div[@class="col-sm-2"]/div[@class="c-directory-list-content"]/div/a/@href').extract()
        for path in city_urls:
            if re.search(r"usa\/[a-z]{2}\/[^\/]+$", path):
                yield scrapy.Request(response.urljoin(path), callback=self.parse_city_stores)
            else:
                yield scrapy.Request(response.urljoin(path), callback=self.parse_stores)
    def parse(self, response):
        urls = response.xpath('//div[@class="row c-directory-list-content-wrapper"]/div[@class="col-sm-2"]/div[@class="c-directory-list-content"]/div/a/@href').extract()
        for path in urls:
            if re.search(r"usa\/[a-z]{2}\/[^\/]+$", path):
                yield scrapy.Request(response.urljoin(path), callback=self.parse_city_stores)
            else:
                yield scrapy.Request(response.urljoin(path), callback=self.parse_state)
