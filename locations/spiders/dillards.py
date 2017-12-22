import scrapy
import re
import json
from locations.items import GeojsonPointItem

DAY_MAPPING = {
    'M': 'Mo',
    'T': 'Tu',
    'W': 'We',
    'F': 'Fr',
    'Sat': 'Sa',
    'Sun': 'Su'
}


class DillardsSpider(scrapy.Spider):

    name = "dillards"
    allowed_domains = ["www.dillards.com"]
    download_delay = 0.5
    start_urls = (
        'https://www.dillards.com/stores',
    )

    def parse_times(self, hour):
        print(hour)
        if hour.strip() == 'Open 24 hours':
            return '24/7'
        if re.search('PM', hour):
                hour = re.sub('PM', '', hour).strip()
                hour_min = hour.split(":")
                if int(hour_min[0]) < 12:
                    hour_min[0] = str(12 + int(hour_min[0]))
                return ":".join(hour_min)
        if re.search('AM', hour):
                hour = re.sub('AM', '', hour).strip()
                hour_min = hour.split(":")
                if len(hour_min[0]) <2:
                    hour_min[0] = hour_min[0].zfill(2)
                else:
                    hour_min[0] = str( int(hour_min[0]))

                return ":".join(hour_min)

    def parse_stores(self, response):
        data =response.xpath('//script[@type="application/ld+json"]/text()').extract_first()
        store = json.loads(response.xpath('//script[@type="application/ld+json"]/text()').extract_first()[:len(data)-4])
        properties = {
            'addr_full': store['location']['address']['streetAddress'],
            'phone':   store['location']['address']['streetAddress'],
            'name': store['name'],
            'city': store['telephone'],
            'state': store['location']['address']['addressRegion'],
            'postcode': store['location']['address']['postalCode'],
            'ref': re.findall(r"[0-9]+$" , response.url)[0],
            'website': response.url,
            'lat': re.findall(r"[0-9.,-]+$" ,response.xpath('//a[@class="direction-link"]/@href').extract_first())[0].split(',')[0],
            'lon': re.findall(r"[0-9.,-]+$" ,response.xpath('//a[@class="direction-link"]/@href').extract_first())[0].split(',')[1],
        }

        hours = ''
        for time in store['openingHoursSpecification']:
            print(time['dayOfWeek']['name'])
            hours = hours + time['dayOfWeek']['name'][:2]+ ' '+self.parse_times(time['opens'])+'-'+self.parse_times(time['closes'])+'; '
        if hours:
            properties['opening_hours'] = hours
        yield GeojsonPointItem(**properties)

    def parse(self, response):
        urls = response.xpath('//span[@class="mallname"]/a/@href').extract()
        for path in urls:
            yield scrapy.Request(response.urljoin(path), callback=self.parse_stores)
