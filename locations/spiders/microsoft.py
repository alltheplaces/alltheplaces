import scrapy
import re
from locations.items import GeojsonPointItem

class MicrosoftSpider(scrapy.Spider):

    name = "microsoft"
    allowed_domains = ["www.microsoft.com"]
    download_delay = 0.5
    start_urls = (
        'https://www.microsoft.com/en-us/store/locations/all-locations',
    )

    def parse_stores(self, response):
        properties = {
            'addr_full': response.xpath('normalize-space(//div[@itemprop="streetAddress"]/span/text())').extract_first(),
            'phone': response.xpath('normalize-space(//div[@itemprop="telephone"]/span/text())').extract_first(),
            'city': response.xpath('normalize-space(//span[@itemprop="addressLocality"]/text())').extract_first(),
            'state': response.xpath('normalize-space(//span[@itemprop="addressRegion"]/text())').extract_first(),
            'postcode': response.xpath('normalize-space(//span[@itemprop="postalCode"]/text())').extract_first().replace(u'\xa0',''),
            'ref': re.findall(r"[^\/]+$" ,response.url)[0],
            'website': response.url,
            'lat': float(response.xpath('normalize-space(//meta[@itemprop="latitude"]/@content)').extract_first()),
            'lon': float(response.xpath('normalize-space(//meta[@itemprop="longitude"]/@content)').extract_first()),
        }

        yield GeojsonPointItem(**properties)


    def parse(self, response):
        urls = response.xpath('//ul[@instancename="Cities list"]/li/a/@href').extract()
        for path in urls:
            yield scrapy.Request(response.urljoin(path), callback=self.parse_stores)
