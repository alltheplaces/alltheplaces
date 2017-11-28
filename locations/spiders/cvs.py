import scrapy
import re
from locations.items import GeojsonPointItem

class CVSSpider(scrapy.Spider):

    name = "cvs"
    allowed_domains = ["www.cvs.com"]
    start_urls = (
        'https://www.cvs.com/store-locator/cvs-pharmacy-locations',
    )

    def parse_hours(self, response):
        store_title = response.xpath('normalize-space(//h4[@class="nomargin store-photo-heading"]/text())').extract_first()
        hours = {}
        if store_title:
            lis = response.xpath('//ul[@class="cleanList srHours srSection"]/li')
            hours [store_title] = {}
            for li in lis:
                day = li.xpath('normalize-space(.//span[@class="day single-day"]/text() | .//span[@class="day"]/text())').extract_first()
                times = li.xpath('.//span[@class="timings"]/text()').extract_first()
                if day and times:
                    hours [store_title].update({day: times})

        phar_title = response.xpath('normalize-space(//h4[@class="printml"]/text())').extract_first()
        if phar_title:
            hours [phar_title] = {}
            phar_hours = response.xpath('//ul[@class="cleanList phHours srSection"]/li')
            for li in phar_hours:
                day = li.xpath('normalize-space(.//span[@class="day single-day"]/text() | .//span[@class="day"]/text())').extract_first()
                times = li.xpath('normalize-space(.//span[@class="timings"]/text())').extract_first()
                if day and times:
                    hours [store_title].update({day: times})
                hours [phar_title].update({day: times})

        return hours


    def parse_stores(self, response):

        addr = response.xpath('normalize-space(//span[@itemprop="streetAddress"]/text())').extract_first()
        locality = response.xpath('normalize-space(//span[@itemprop="addressLocality"]/text())').extract_first()
        state = response.xpath('normalize-space(//span[@itemprop="addressRegion"]/text())').extract_first()
        postalCode = response.xpath('normalize-space(//span[@itemprop="postalCode"]/text())').extract_first()
        raw_phone = response.xpath('normalize-space(//a[@class="tel_phone_numberDetail"]/@href)').extract_first()
        phone = re.sub('tel:', '', raw_phone)
        ref = response.xpath('//link[@rel="canonical"]/@href').extract_first()

        latitude = float(response.xpath('normalize-space(//input[@id="toLatitude"]/@value)').extract_first())
        longitude = float(response.xpath('normalize-space(//input[@id="toLongitude"]/@value)').extract_first())

        lat_long = [latitude, longitude]
        hours = self.parse_hours(response)

        properties = {'addr:full': addr, 'phone': phone, 'addr:city': locality,
                      'addr:state': state, 'addr:postcode': postalCode,
                      'ref': ref, 'website:': ref, 'opening_hours': hours,
                     }

        yield GeojsonPointItem(
            properties=properties,
            lon_lat=lat_long
        )

    def parse_city_stores(self, response):
        stores = response.xpath('//div[@class="each-store"]')

        for store in stores:

            direction = store.xpath('normalize-space(.//span[@class="store-number"]/a/@href)').extract_first()
            if direction:
                yield scrapy.Request(response.urljoin(direction), callback=self.parse_stores)


    def parse_state(self, response):    
        city_urls = response.xpath('//div[@class="states"]/ul/li/a/@href').extract()
        for path in city_urls:
            yield scrapy.Request(response.urljoin(path), callback=self.parse_city_stores)

    def parse(self, response):
        urls = response.xpath('//div[@class="states"]/ul/li/a/@href').extract()
        for path in urls:
            yield scrapy.Request(response.urljoin(path), callback=self.parse_state)
