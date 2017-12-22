import scrapy
import re
from locations.items import GeojsonPointItem
class NordstromSpider(scrapy.Spider):

    name = "nordstrom"
    allowed_domains = ["shop.nordstrom.com"]
    download_delay = 0
    start_urls = (
        'https://shop.nordstrom.com/c/sitemap-stores',
    )

    def parse_stores(self, response):
        lat = re.findall(r'\"Latitude\":\"[0-9-.]+' ,response.body_as_unicode())[0]
        lng = re.findall(r'\"Longitude\":\"[0-9-.]+' ,response.body_as_unicode())[0]
        lat = re.findall(r"[0-9.-]+$",lat)[0]
        lng = re.findall(r"[0-9.-]+$",lng)[0]
        properties = {
            'addr_full': response.xpath('normalize-space(//span[@itemprop="streetAddress"]/text())').extract_first().replace(',' ,''),
            'phone': response.xpath('normalize-space(//span[@itemprop="telephone"]/text())').extract_first(),
            'city': response.xpath('normalize-space(//span[@itemprop="addressLocality"]/text())').extract_first().replace(',' ,''),
            'state': response.xpath('normalize-space(//span[@itemprop="addressRegion"]/text())').extract_first(),
            'postcode': response.xpath('normalize-space(//span[@itemprop="postalCode"]/text())').extract_first(),
            'ref': response.xpath('normalize-space(//div[@class="store-number"]/text())').extract_first(),
            'website': response.url,
            'lat': float(lat),
            'lon': float(lng),
        }
        yield GeojsonPointItem(**properties)

    def parse(self, response):
        urls = response.xpath('//a[contains(@href ,"shop.nordstrom.com/st/")]/@href').extract()
        for path in urls:
            yield scrapy.Request(response.urljoin(path), callback=self.parse_stores)
