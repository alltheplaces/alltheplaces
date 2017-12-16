# -*- coding: utf-8 -*-
import scrapy
import json
import re
from locations.items import GeojsonPointItem

class AldiAUSpider(scrapy.Spider):
    name = 'aldi_au'
    allowed_domains = ['www.yellowmap.de']
    start_urls = (
        'https://www.yellowmap.de/Presentation/AldiSued/en-AU/ResultList?LocX=&LocY=&HiddenBranchCode=&BranchCode=&Lux=120.146484375&Luy=1.4939713066293239&Rlx=152.138671875&Rly=-46.73986059969267&ZoomLevel=4',
    )
    
    def parse(self, response):
        data = json.loads(response.body_as_unicode())
        container = data['Container']
        stores = self.parse_data(container)

        for store in stores:
            json_data = json.loads(store.css('.resultItem::attr(data-json)').extract_first())
            ref = json_data['id']
            lat = json_data['locY']
            lon = json_data['locX']
            name = store.css('.resultItem-CompanyName::text').extract_first()
            street = store.css('.resultItem-Street::text').extract_first()
            address1 = store.css('.resultItem-City::text').extract_first().split(',')
            hours_data = store.css('.openingHoursTable > tr')
            
            pattern = r'(.*)(\s\w{1,3}\s)(.*)'
            if len(address1) == 2: 
                city = address1[0].strip()
                match = re.search(pattern, address1[1])
                state = match.groups()[1]
                zipcode = match.groups()[2]
            elif len(address1) == 1 :
                match = re.search(pattern, address1[0])
                if match is not None:
                    city, state, zipcode = match.groups()
                else:
                    match = re.search(r'(.*?)(\d+)', address1[0])
                    city, zipcode = match.groups()
                    state = ''

            properties = {
                'ref': ref,
                'name': name,
                'opening_hours': self.hours(hours_data),
                'lat': lat,
                'lon': lon,
                'street': street.strip(),
                'city': city.strip(),
                'state': state.strip(),
                'postcode': zipcode.strip()
            }

            yield GeojsonPointItem(**properties)

        if 'zoom' in response.meta.keys():
            zoom = response.meta["zoom"]
        else:
            zoom = 6

        for child in self.children(container):
            yield scrapy.Request(
                'https://www.yellowmap.de/Presentation/AldiSued/en-AU/ResultList?LocX={}&LocY={}&ZoomLevel={}'.format(child['locX'], child['locY'], zoom),
                meta = {'zoom' : zoom + 2},
                callback = self.parse
            )

    def children(self, data):
        json_data = re.search(r'(Tiles:) (\[{.*}\])', data)
        if json_data:
            return json.loads(json_data.groups()[1])
        else: 
            return []

    def parse_data(self, data):
        data = scrapy.http.HtmlResponse(url = '', body = data, encoding='utf-8')
        stores = data.css('.resultItem')
        if stores:
            return stores
        else:
            return []

    def hours(self, data):
        opening_hours = ''
        for day_group in data:
            time = day_group.css('td::text').extract()
            day = time[0].strip()
            hours = time[1].strip()

            if '-' in day :
                f_day = day.split('-')[0].strip()[:2]
                t_day = day.split('-')[1].strip()[:2]
                day = '{}-{}'.format(f_day, t_day)
            else:
                day = day[:2]
            if hours.lower() == 'closed' :
                opening_hours += '{} {};'.format(
                    day,
                    hours
                )
            else :
                f_hour_text = hours.split('-')[0].strip()
                t_hour_text = hours.split('-')[1].strip()
                f_hour = self.normalize_time(f_hour_text)
                t_hour = self.normalize_time(t_hour_text)
                opening_hours += '{} {}; '.format(
                    day,
                    '{}-{}'.format(f_hour, t_hour)
                )

        return opening_hours

    def normalize_time(self, time_str):
        match = re.search(r'([0-9]{1,2}):([0-9]{1,2}) (A|P)M$', time_str)
        if not match:
            match = re.search(r'([0-9]{1,2}) (A|P)M$', time_str)
            h, am_pm = match.groups()
            m = "0"
        else:
            h, m, am_pm = match.groups()

        return '%02d:%02d' % (
            int(h) + 12 if am_pm == 'P' else int(h),
            int(m),
        )



            




    
