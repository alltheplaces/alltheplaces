# -*- coding: utf-8 -*-
import scrapy
import re

from locations.items import GeojsonPointItem


class GoddardSchoolSpider(scrapy.Spider):
    name = "goddard_school"
    allowed_domains = ["www.goddardschool.com"]
    start_urls = (
        'https://www.goddardschool.com/LocationsXML.aspx',
    )

    def store_hours(self, hours_string):
        match = re.match(r'^(\w+) - (\w+): (\d{1,2}):(\d{2}) (am|pm) - (\d{1,2}):(\d{2}) (am|pm)$', hours_string)
        (f_dow, t_dow, f_hr, f_min, f_ampm, t_hr, t_min, t_ampm) = match.groups()

        f_hr = int(f_hr)
        f_min = int(f_min)
        t_hr = int(t_hr)
        t_min = int(t_min)

        if f_ampm == 'pm':
            f_hr = int(f_hr) + 12
        if t_ampm == 'pm':
            t_hr = int(t_hr) + 12

        return '{}-{} {:02d}:{:02d}-{:02d}:{:02d}'.format(
            f_dow[:2],
            t_dow[:2],
            f_hr,
            f_min,
            t_hr,
            t_min,
        )

    def parse(self, response):
        for marker_elem in response.xpath('//marker'):
            yield scrapy.Request(
                response.urljoin(marker_elem.xpath('@url')[0].extract()),
                callback=self.parse_location,
                meta={
                    'ref': marker_elem.xpath('@id')[0].extract(),
                    'name': marker_elem.xpath('@name')[0].extract(),
                    'addr:full': marker_elem.xpath('@address')[0].extract(),
                    'addr:city': marker_elem.xpath('@city')[0].extract(),
                    'addr:state': marker_elem.xpath('@state')[0].extract(),
                    'addr:postcode': marker_elem.xpath('@zip')[0].extract(),
                    'phone': marker_elem.xpath('@phone')[0].extract(),
                    'lat': marker_elem.xpath('@lat')[0].extract(),
                    'lng': marker_elem.xpath('@lng')[0].extract(),
                }
            )

    def parse_location(self, response):
        properties = {
            'addr:full': response.meta['addr:full'],
            'addr:city': response.meta['addr:city'],
            'addr:state': response.meta['addr:state'],
            'addr:postcode': response.meta['addr:postcode'],
            'ref': response.meta['ref'],
            'website': response.url,
        }

        hours_elem = response.xpath('//span[@itemprop="hours"]/text()')
        if hours_elem:
            properties['opening_hours'] = self.store_hours(hours_elem[0].extract())

        lon_lat = [
            float(response.meta['lng']),
            float(response.meta['lat']),
        ]

        yield GeojsonPointItem(
            properties=properties,
            lon_lat=lon_lat,
        )
