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


class CVSSpider(scrapy.Spider):

    name = "cvs"
    allowed_domains = ["www.cvs.com"]
    download_delay = 1.5
    start_urls = (
        'https://www.cvs.com/store-locator/cvs-pharmacy-locations',
    )

    def parse_day(self, day):

        if re.search('Sat', day) or re.search('Sun', day):
            return DAY_MAPPING[day.strip()]

        if re.search('-', day):
            days = day.split('-')
            osm_days = []
            if len(days) == 2:
                for day in days:
                    osm_day = DAY_MAPPING[day.strip()]
                    osm_days.append(osm_day)
            return "-".join(osm_days)

    def parse_times(self, times):
        if times.strip() == 'Open 24 hours':
            return '24/7'
        hours_to = [x.strip() for x in times.split('-')]
        cleaned_times = []

        for hour in hours_to:
            if re.search('PM$', hour):
                hour = re.sub('PM', '', hour).strip()
                hour_min = hour.split(":")
                if int(hour_min[0]) < 12:
                    hour_min[0] = str(12 + int(hour_min[0]))
                cleaned_times.append(":".join(hour_min))

            if re.search('AM$', hour):
                hour = re.sub('AM', '', hour).strip()
                hour_min = hour.split(":")
                if len(hour_min[0]) <2:
                    hour_min[0] = hour_min[0].zfill(2)
                else:
                    hour_min[0] = str(12 + int(hour_min[0]))

                cleaned_times.append(":".join(hour_min))
        return "-".join(cleaned_times)

    def parse_hours(self, lis):
        hours = []
        for li in lis:
            day = li.xpath('normalize-space(.//span[@class="day single-day"]/text() | .//span[@class="day"]/text())').extract_first()
            times = li.xpath('.//span[@class="timings"]/text()').extract_first()
            if times and day:
                parsed_time = self.parse_times(times)
                parsed_day = self.parse_day(day)
                hours.append(parsed_day + ' ' + parsed_time)

        return "; ".join(hours)

    def parse_stores(self, response):
        raw_phone = response.xpath('normalize-space(//a[@class="tel_phone_numberDetail"]/@href)').extract_first()

        properties = {
            'addr_full': response.xpath('normalize-space(//span[@itemprop="streetAddress"]/text())').extract_first(),
            'phone': raw_phone.replace('tel:', ''),
            'city': response.xpath('normalize-space(//span[@itemprop="addressLocality"]/text())').extract_first(),
            'state': response.xpath('normalize-space(//span[@itemprop="addressRegion"]/text())').extract_first(),
            'postcode': response.xpath('normalize-space(//span[@itemprop="postalCode"]/text())').extract_first(),
            'ref': response.xpath('//link[@rel="canonical"]/@href').extract_first(),
            'website': response.xpath('//link[@rel="canonical"]/@href').extract_first(),
            'lat': float(response.xpath('normalize-space(//input[@id="toLatitude"]/@value)').extract_first()),
            'lon': float(response.xpath('normalize-space(//input[@id="toLongitude"]/@value)').extract_first()),
        }

        hours = self.parse_hours(response.xpath('//ul[@class="cleanList srHours srSection"]/li'))
        if hours:
            properties['opening_hours'] = hours

        yield GeojsonPointItem(**properties)

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
