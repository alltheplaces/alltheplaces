import scrapy
import re
from locations.items import GeojsonPointItem
class AdvanceautopartsSpider(scrapy.Spider):

    name = "advanceautoparts"
    allowed_domains = ["stores.advanceautoparts.com"]
    download_delay = 0.1
    start_urls = (
        'https://stores.advanceautoparts.com/index.html#DirectoryList',
    )

    def parse_stores(self, response):
        brand = response.xpath('//span[@class="LocationName-brand"]/span/text()').extract_first()
        ref = brand.replace("#","").strip()

        properties = {
            'addr_full': response.xpath('normalize-space(//meta[@itemprop="streetAddress"]/@content)').extract_first(),
            'phone': response.xpath(
                'normalize-space(//span[@itemprop="telephone"]/text())').extract_first(),
            'city': response.xpath('normalize-space(//span[@itemprop="addressLocality"]/text())').extract_first(),
            'state': response.xpath('normalize-space(//abbr[@itemprop="addressRegion"]/text())').extract_first(),
            'postcode': response.xpath('normalize-space(//span[@itemprop="postalCode"]/text())').extract_first(),
            'ref': ref,
            'website': response.url,
            'lat': response.xpath('normalize-space(//meta[@itemprop="latitude"]/@content)').extract_first(),
            'lon': response.xpath('normalize-space(//meta[@itemprop="longitude"]/@content)').extract_first(),
            'name': response.xpath('//div[@class="LocationName-geo"]/text()').extract_first(),
        }
        hours = response.xpath('//div[@class="Nap-hours Text Text--xsmall Text--gray"]/div[@class="c-location-hours"]/div[@class="c-location-hours-details-wrapper js-location-hours"]/table/tbody/tr/@content').extract()
        if hours !=[]:
            hours = " ; ".join(hours)
            properties['opening_hours'] = hours
        yield GeojsonPointItem(**properties)

    def parse_city_stores(self, response):
        stores = response.xpath('//h3[@class="Teaser-title Link Link--teaser Heading--h5"]/a/@href').extract()
        for store in stores:
            yield scrapy.Request(response.urljoin(store), callback=self.parse_stores)

    def parse_state(self, response):
        urls = response.xpath('//div[@class="c-directory-list-content-wrapper"]/ul/li/a/@href').extract()
        for path in urls:
            pattern = re.compile("^[a-z]{2}\/[^()]+\/[^()]+$")
            if (pattern.match(path.strip())):
                yield scrapy.Request(response.urljoin(path), callback=self.parse_stores)
            else:
                yield scrapy.Request(response.urljoin(path), callback=self.parse_city_stores)

    def parse(self, response):
        urls = response.xpath('//div[@class="c-directory-list-content-wrapper"]/ul/li/a/@href').extract()
        for path in urls:
            pattern = re.compile("^[a-z]{2}$")
            pattern1 = re.compile("^[a-z]{2}\/[^()]+\/[^()]+$")

            if (pattern.match(path.strip())):
                yield scrapy.Request(response.urljoin(path), callback=self.parse_state)
            elif (pattern1.match(path.strip())):
                yield scrapy.Request(response.urljoin(path), callback=self.parse_stores)
            else:
                yield scrapy.Request(response.urljoin(path), callback=self.parse_city_stores)
