# -*- coding: utf-8 -*-
import scrapy
import re
from locations.items import GeojsonPointItem

STATES = ['AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DC', 'DE', 'FL', 'GA',
          'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
          'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
          'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
          'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY']

class UhaulSpider(scrapy.Spider):
    name = "uhaul"
    allowed_domains = ["www.uhaul.com"]
        
    def start_requests(self):
        for state in STATES:
            url = 'https://www.uhaul.com/Locations/{}/Results/?page=1'.format(
                state
            )
            yield scrapy.Request(
                url,
                callback=self.parse
            )

    def parse(self, response):
        sections = response.css('#locationsResults .divider')
        if sections:
            next = sections[-1].css('#locationSearchNextLocations::attr(href)')

            for section in sections[:-1]:
                name = section.css('.map-location a::text').extract_first()
                website = section.css('.map-location a::attr(href)').extract_first()
                ref = website.split('/')[-2]
                addr_data = section.css('.row .medium-8.columns .collapse::text').extract()
                phone = section.css('.row .medium-8.columns .no-bullet li a::attr(href)').extract_first()[4:]
                street = addr_data[1].strip()
                city, state, zipcode = re.search(r'(.*), (.*) (\d+)', addr_data[2]).groups()
                hours_data = section.css('.row .medium-6.columns .row .medium-6.columns .no-bullet')[0]
                
                properties = {
                    'ref': ref,
                    'name': name,
                    'website': website,
                    'street': street,
                    'opening_hours': self.hours(hours_data),
                    'city': city.strip(),
                    'state': state,
                    'postcode': zipcode
                }

                yield GeojsonPointItem(**properties)
            if next:
                yield scrapy.Request(
                    'https://www.uhaul.com' + next.extract_first(),
                    callback = self.parse
                )

    def hours(self, store_hours):
        store_hours = store_hours.css('li::text').extract()
        opening_hours = ''

        for data in store_hours:
            day_text = data.split(':')[0]
            hours_text = data.split(':')[1]

            if '-' in day_text:
                f_day = day_text.split('-')[0][:2]
                t_day = day_text.split('-')[1][:2]
                day = '{}-{}'.format(f_day, t_day)
            else:
                day = day_text[:2]

            if '-' in hours_text:
                f_hour = self.normalize_time(hours_text.split('-')[0].strip(), True)
                t_hour = self.normalize_time(hours_text.split('-')[1].strip(), False)
                hours = '{}-{}'.format(f_hour, t_hour)
            else:
                hours = 'Closed'

            opening_hours = opening_hours + '{} {}; '.format(day, hours)
        
        return opening_hours

    def normalize_time(self, time_str, open):
        match = re.search(r'([0-9]{1,2}):([0-9]{1,2})', time_str)
        if not match:
            match = re.search(r'([0-9]{1,2})', time_str)
            h = match.group()
            m = '0'
        else:
            h, m = match.groups()

        return '%02d:%02d' % (
            int(h) + 12 if not open else int(h),
            int(m),
        )