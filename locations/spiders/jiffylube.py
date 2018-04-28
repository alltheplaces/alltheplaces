# -*- coding: utf-8 -*-
import scrapy
import re

from locations.items import GeojsonPointItem

STATES = [
    'AL', 'AK', 'AS', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'DC', 'FM', 'FL',
    'GA', 'GU', 'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MH',
    'MD', 'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ', 'NM',
    'NY', 'NC', 'ND', 'MP', 'OH', 'OK', 'OR', 'PW', 'PA', 'PR', 'RI', 'SC',
    'SD', 'TN', 'TX', 'UT', 'VT', 'VI', 'VA', 'WA', 'WV', 'WI', 'WY'
]

class JiffyLubeSpider(scrapy.Spider):
    name = "jiffylube"
    allowed_domains = ["www.jiffylube.com"]

    def start_requests(self):
        base_url = 'https://www.jiffylube.com/locations'
        for state in STATES:
            yield scrapy.Request(
                '{}/{}'.format(base_url, state)
            )

    def store_hours(self, store_hours):
        opening_hours = []
        for day_hours in store_hours:
            day_hours = day_hours.replace('Mon', 'Mo').replace('Tue', 'Tu').replace('Wed', 'We').replace('Thu', 'Th').replace('Fri', 'Fr').replace('Sat', 'Sa').replace('Sun', 'Su')
            day_hours = day_hours.replace('Weekdays', 'Mo-Fr').replace('Weekends', 'Sa-Su').replace('Holidays', 'PH').replace('Everyday', 'Mo-Su')
            day_hours = day_hours.replace('midnight', '12 PM').replace(':', '')
            hours = ''
            match = re.search(r'(\d{1,2}) (A|P)M - (\d{1,2}) (A|P)M', day_hours)
            if match:
                (f_hr, f_ampm, t_hr, t_ampm) = match.groups()
                f_hr = int(f_hr)
                if f_ampm == 'P':
                    f_hr += 12
                elif f_ampm == 'A' and f_hr == 12:
                    f_hr = 0
                t_hr = int(t_hr)
                if t_ampm == 'P':
                    t_hr += 12
                elif t_ampm == 'A' and t_hr == 12:
                    t_hr = 0
                
                hours = '{:02d}:{}-{:02d}:{}'.format(
                    f_hr,
                    '00',
                    t_hr,
                    '00',
                )
                day_hours = day_hours.replace(match.group(), hours)
            opening_hours.append(day_hours)
        return "; ".join(opening_hours)
    
    def parse(self, response):
        stores = response.xpath('//div[@class="locations-by-state"]/div[@class="state-locations"]')
        for store in stores:
            url = store.xpath('div[@class="state-location-info"]/a[@class="title"]/@href').extract_first()
            yield scrapy.Request(response.urljoin(url), callback=self.parse_stores)

    def parse_stores(self, response):
        store = response.xpath('//div[@class="location-information"]')
        name = response.xpath('//div[@class="location--singleLocation"]/h1[@class="location-title"]/text()[last()]').extract_first()
        match = re.search(r'\#(\d+)', name)
        ng_script = response.xpath('//div[@class="container group"]/@data-ng-init').extract_first()
        coor_match = re.search(r'latitude":(-?\d+\.\d+),"longitude":(-?\d+\.\d+)', ng_script)

        properties = {
            'ref': match.group(1),
            'name': name,
            'addr_full': store.xpath('div[@class="location-information-address"]/a/div[1]/span/text()').extract_first(),
            'city': store.xpath('div[@class="location-information-address"]/a/div[2]/span[1]/text()').extract_first(),
            'state': store.xpath('div[@class="location-information-address"]/a/div[2]/span[2]/text()').extract_first(),
            'postcode': store.xpath('div[@class="location-information-address"]/a/div[2]/span[3]/text()').extract_first(),
            'phone': store.xpath('div[@class="location-information-phoneNumber"]/strong/span/a/text()').extract_first(),
            'lat': coor_match.group(1),
            'lon': coor_match.group(2),
            'opening_hours': self.store_hours(store.xpath('div[@class="location-information-hours"]/div[@itemprop="openingHours"]/text()').extract()),
        }

        yield GeojsonPointItem(**properties)    