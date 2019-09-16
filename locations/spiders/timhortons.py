import scrapy
import re
from locations.items import GeojsonPointItem


class TimhortonsSpider(scrapy.Spider):
    name = "timhortons"
    allowed_domains = ["locations.timhortons.com"]
    custom_settings = {
        'DUPEFILTER_CLASS': 'scrapy.dupefilters.BaseDupeFilter',
    }
    download_delay = 0
    start_urls = (
        'https://locations.timhortons.com/',
    )

    def parse_stores(self, response):
        name1 = response.xpath('//span[@class="LocationName-brand"]//text()').extract_first()
        name2 = response.xpath('//span[@class="LocationName-geo"]//text()').extract_first()
        name = name1 + ' ' + name2

        properties = {
            'ref': response.url,
            'name': name,
            'lat': response.xpath('normalize-space(//meta[@itemprop="latitude"]/@content)').extract_first(),
            'lon': response.xpath('normalize-space(//meta[@itemprop="longitude"]/@content)').extract_first(),
            'addr_full': response.xpath('normalize-space(//meta[@itemprop="streetAddress"]/@content)').extract_first(),
            'city': response.xpath('normalize-space(//span[@itemprop="addressLocality"]/text())').extract_first(),
            'state': response.xpath('normalize-space(//abbr[@itemprop="addressRegion"]/text())').extract_first(),
            'country': response.xpath('//address[@class="c-address"]/@data-country').extract_first(),
            'postcode': response.xpath('normalize-space(//span[@itemprop="postalCode"]/text())').extract_first(),
            'website': response.url,
            'phone': response.xpath(
                'normalize-space(//div[@class="Nap-phone"]/div[@class="c-phone-number c-phone-main-number"]/a[@class="c-phone-number-link c-phone-main-number-link"]/text())').extract_first()
        }

        yield GeojsonPointItem(**properties)

    def parse_city_stores(self, response):
        stores = response.xpath(
            '//*[@class="Teaser-titleLink" and @data-ya-track!="nearby_locations"]/@href').extract()
        if len(stores) != 0:
            for store in stores:
                yield scrapy.Request(response.urljoin(store), callback=self.parse_stores)
        else:
            yield scrapy.Request(response.url, callback=self.parse_stores)

    def parse_city(self, response):
        try:
            cities = response.xpath('//*[@class="c-directory-list-content-item"]/a/@href').extract()
            for city in cities:
                yield scrapy.Request(response.urljoin(city), callback=self.parse_city_stores)
        except:
            yield scrapy.Request(response.url, callback=self.parse_city_stores)

    def parse_state(self, response):
        urls = response.xpath('//div[@class="c-directory-list-content-wrapper"]/ul/li/a/@href').extract()
        for path in urls:
            pattern = re.compile("^[a-z]{2}\/[^()]+\/[^()]+.html$")
            if (pattern.match(path.strip())):
                yield scrapy.Request(response.urljoin(path), callback=self.parse_city_stores)
            else:
                yield scrapy.Request(response.urljoin(path), callback=self.parse_city)

    def parse(self, response):
        urls = response.xpath('//div[@class="c-directory-list-content-wrapper"]/ul/li/a/@href').extract()
        for path in urls:
            yield scrapy.Request(response.urljoin(path), callback=self.parse_state)
