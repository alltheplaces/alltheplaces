import scrapy
import re
from locations.items import GeojsonPointItem

class NikeSpider(scrapy.Spider):

    name = "nike"
    allowed_domains = ["www.nike.com"]
    download_delay = 1.5
    start_urls = (
        'https://www.nike.com/us/en_us/retail/en/directory',
    )

    def parse_stores(self, response):
        properties = {
            'name': response.xpath('normalize-space(//meta[@itemprop="name"]/@content)').extract_first(),
            'addr_full': response.xpath('normalize-space(//meta[@itemprop="streetAddress"]/@content)').extract_first(),
            'phone': response.xpath('normalize-space(//meta[@itemprop="telephone"]/@content)').extract_first(),
            'city': response.xpath('normalize-space(//meta[@itemprop="addressLocality"]/@content)').extract_first(),
            'state': response.xpath('normalize-space(//meta[@itemprop="addressRegion"]/@content)').extract_first(),
            'postcode': response.xpath('normalize-space(//meta[@itemprop="postalCode"]/@content)').extract_first(),
            'ref': re.findall(r"[^\/]+$" ,response.url)[0],
            'website': response.url,
            'lat': float(response.xpath('normalize-space(//meta[@itemprop="latitude"]/@content)').extract_first()),
            'lon': float(response.xpath('normalize-space(//meta[@itemprop="longitude"]/@content)').extract_first()),
        }
        yield GeojsonPointItem(**properties)

    def parse(self, response):
        urls = response.xpath('//div[@class="bwt-directory-store-wrapper bwt-hide-on-mobile"]/a/@href').extract()
        for path in urls:
            yield scrapy.Request(response.urljoin(path), callback=self.parse_stores)
