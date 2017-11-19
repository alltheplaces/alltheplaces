# -*- coding: utf-8 -*-
import scrapy
import re

from locations.items import GeojsonPointItem


class ChickFilASpider(scrapy.Spider):
    name = "chickfila"
    allowed_domains = ["www.chick-fil-a.com"]
    start_urls = (
        'https://www.chick-fil-a.com/Locations/Browse',
    )

    def store_hours(self, hours_elem):
        dow_elems = hours_elem.xpath('dt/text()')
        time_elems = hours_elem.xpath('dd/text()')

        day_groups = []
        this_day_group = None
        for dow_elem, time_elem in zip(dow_elems, time_elems):
            dow = dow_elem.extract()
            timerange = time_elem.extract()

            if timerange == 'Closed':
                continue

            dow_split = dow.split(' - ')
            if len(dow_split) == 2:
                fm_dow = dow_split[0][:2]
                to_dow = dow_split[1][:2]
            else:
                fm_dow = dow_split[0][:2]
                to_dow = dow_split[0][:2]

            match = re.search(r'^(\d{1,2}):(\d{2}) ([APM]{2})-(\d{1,2}):(\d{2}) ([APM]{2})$', timerange)
            (f_hr, f_min, f_ampm, t_hr, t_min, t_ampm) = match.groups()

            f_hr = int(f_hr)
            if f_ampm == 'PM':
                f_hr += 12
            elif f_ampm == 'AM' and f_hr == 12:
                f_hr = 0
            t_hr = int(t_hr)
            if t_ampm == 'PM':
                t_hr += 12
            elif t_ampm == 'AM' and t_hr == 12:
                t_hr = 0

            hours = '{:02d}:{}-{:02d}:{}'.format(
                f_hr,
                f_min,
                t_hr,
                t_min,
            )

            if not this_day_group:
                this_day_group = dict(from_day=fm_dow, to_day=to_dow, hours=hours)
            elif this_day_group['hours'] == hours:
                this_day_group['to_day'] = to_dow
            elif this_day_group['hours'] != hours:
                day_groups.append(this_day_group)
                this_day_group = dict(from_day=fm_dow, to_day=to_dow, hours=hours)
        day_groups.append(this_day_group)

        if len(day_groups) == 1:
            opening_hours = day_groups[0]['hours']
            if opening_hours == '07:00-07:00':
                return '24/7'

        opening_hours = ''
        for day_group in day_groups:
            if day_group['from_day'] == day_group['to_day']:
                opening_hours += '{from_day} {hours}; '.format(**day_group)
            else:
                opening_hours += '{from_day}-{to_day} {hours}; '.format(**day_group)
        opening_hours = opening_hours[:-2]

        return opening_hours

    def address(self, response):
        addr_text = response.xpath('//div[@class="location-details"]/p[@class="address"]/text()').extract_first()
        addr_text = addr_text.strip().replace('\n', ' ')

        addr_split = addr_text.split(' , ')
        addr_split = [a.strip() for a in addr_split]
        if len(addr_split) == 4:
            (street, street2, city, statezip) = addr_split
        else:
            (street, city, statezip) = addr_split

        (state, postcode) = list(filter(None, statezip.split(' ')))

        return {
            'addr:full': street,
            'addr:city': city,
            'addr:state': state,
            'addr:postcode': postcode,
        }

    def parse(self, response):
        for state_elem in response.xpath('//article/ul/li/a/@href'):
            yield scrapy.Request(
                response.urljoin(state_elem.extract()),
                callback=self.parse_state,
            )

    def parse_state(self, response):
        for city_elem in response.xpath('//div[@class="location"]/h2/a/@href'):
            yield scrapy.Request(
                response.urljoin(city_elem.extract()),
                callback=self.parse_location,
            )

    def parse_location(self, response):
        ref = response.xpath('//a[@class="btn set-as-location"]/@data-loc-id').extract_first() \
              or response.request.url

        properties = {
            "phone": response.xpath('//div[@class="module"]/p/a/text()').extract_first(),
            "ref": ref,
            "name": response.xpath('//div[@class="location-details"]/h1/text()').extract_first(),
            "opening_hours": self.store_hours(response.xpath('//dl[@class="hours"]')[0]),
        }

        properties.update(self.address(response))

        lon_lat = [
            float(response.xpath('//span[@id="currentlocdistanceid"]/@data-long').extract_first()),
            float(response.xpath('//span[@id="currentlocdistanceid"]/@data-lat').extract_first()),
        ]

        yield GeojsonPointItem(
            properties=properties,
            lon_lat=lon_lat,
        )
