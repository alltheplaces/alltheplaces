import scrapy
import re
from locations.items import GeojsonPointItem

class TimhortonsSpider(scrapy.Spider):

    name = "timhortons"
    allowed_domains = ["locations.timhortons.com"]
    download_delay = 0
    start_urls = (
        'https://locations.timhortons.com/?q_loc=',
    )
    def parse_stores(self, response):
        ref = re.findall(r"[^(\/)]+.html$" ,response.url)
        if(len(ref)>0):
            ref = ref[0].split('.')[0]
        properties = {
            'addr_full': response.xpath('normalize-space(//meta[@itemprop="streetAddress"]/@content)').extract_first(),
            'phone': response.xpath('normalize-space(//div[@class="Nap-phone"]/div[@class="c-phone-number c-phone-main-number"]/a[@class="c-phone-number-link c-phone-main-number-link"]/text())').extract_first(),
            'city': response.xpath('normalize-space(//span[@itemprop="addressLocality"]/text())').extract_first(),
            'state': response.xpath('normalize-space(//abbr[@itemprop="addressRegion"]/text())').extract_first(),
            'postcode': response.xpath('normalize-space(//span[@itemprop="postalCode"]/text())').extract_first(),
            'ref': ref,
            'website': response.url,
            'lat':  response.xpath('normalize-space(//meta[@itemprop="latitude"]/@content)').extract_first(),
            'lon':  response.xpath('normalize-space(//meta[@itemprop="longitude"]/@content)').extract_first(),
        }
        yield GeojsonPointItem(**properties)
    def parse_city_stores(self ,response):
        stores = response.xpath('//div[@class="Teaser-headerWrapper"]/h2/a/@href').extract()
        for store in stores:
                yield scrapy.Request(response.urljoin(store), callback=self.parse_stores)

    def parse_state(self, response):
        urls = response.xpath('//div[@class="c-directory-list-content-wrapper"]/ul/li/a/@href').extract()
        for path in urls:
            pattern = re.compile("^[a-z]{2}\/[^()]+\/[^()]+.html$")
            if (pattern.match(path.strip())):
                yield scrapy.Request(response.urljoin(path), callback=self.parse_stores)
            else:
                yield scrapy.Request(response.urljoin(path), callback=self.parse_city_stores)

    def parse(self, response):
        urls = response.xpath('//div[@class="c-directory-list-content-wrapper"]/ul/li/a/@href').extract()
        for path in urls:
            pattern = re.compile("^[a-z]{2}.html$")
            pattern1 = re.compile("^[a-z]{2}\/[^()]+\/[^()]+.html$")
            if(pattern.match(path.strip())):
               yield scrapy.Request(response.urljoin(path), callback=self.parse_state)
            elif(pattern1.match(path.strip())):
                yield scrapy.Request(response.urljoin(path), callback=self.parse_stores)
            else:
                yield scrapy.Request(response.urljoin(path), callback=self.parse_city_stores)
