# -*- coding: utf-8 -*-
import scrapy
import json

from locations.items import GeojsonPointItem


class HomeDepotSpider(scrapy.Spider):
    name = "homedepot"
    allowed_domains = ["www.homedepot.com"]
    start_urls = (
        'https://www.homedepot.com/l/storeDirectory',
    )

    def store_hours(self, store_hours):
        day_groups = []
        this_day_group = None
        for day in ('monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'):
            day_open = store_hours[day]['open'].zfill(5)
            day_close = store_hours[day]['close'].zfill(5)

            hours = day_open + "-" + day_close

            if hours == '00:00-00:00':
                # They're closed on this day
                continue

            day_short = day.title()[:2]

            if not this_day_group:
                this_day_group = dict(from_day=day_short, to_day=day_short, hours=hours)
            elif this_day_group['hours'] == hours:
                this_day_group['to_day'] = day_short
            elif this_day_group['hours'] != hours:
                day_groups.append(this_day_group)
                this_day_group = dict(from_day=day_short, to_day=day_short, hours=hours)
        day_groups.append(this_day_group)

        if not day_groups:
            return None

        if len(day_groups) == 1:
            opening_hours = day_groups[0]['hours']
            if opening_hours == '07:00-07:00':
                opening_hours = '24/7'
        else:
            opening_hours = ''
            for day_group in day_groups:
                if day_group['from_day'] == day_group['to_day']:
                    opening_hours += '{from_day} {hours}; '.format(**day_group)
                else:
                    opening_hours += '{from_day}-{to_day} {hours}; '.format(**day_group)
            opening_hours = opening_hours[:-2]

        return opening_hours

    def parse(self, response):
        for path in response.xpath('//a[@class="stateList__link"]/@href'):
            yield scrapy.Request(
                response.urljoin(path.extract()),
                callback=self.parse_state,
            )

    def parse_state(self, response):
        for path in response.xpath('//a[@class="storeList__link"]/@href'):
            if not path.extract()[-1].isdigit():
                continue

            yield scrapy.Request(
                response.urljoin(path.extract()),
                callback=self.parse_store,
            )

    def parse_store(self, response):
        # There's extra JSON loading stuff before and after the JSON blob to skip around
        data = json.loads(response.xpath('//script/text()').extract_first()[81:-686])
        store_data = data['stores'][0]

        properties = {
            'phone': store_data['phone'],
            'website': response.urljoin(store_data['url']),
            'ref': store_data['storeId'],
            'name': store_data['name'],
            'addr:full': store_data['address']['street'],
            'addr:postcode': store_data['address']['postalCode'],
            'addr:state': store_data['address']['state'],
            'addr:city': store_data['address']['city'],
        }

        opening_hours = self.store_hours(store_data['storeHours'])
        if opening_hours:
            properties['opening_hours'] = opening_hours

        lon_lat = [
            float(store_data['coordinates']['lng']),
            float(store_data['coordinates']['lat']),
        ]

        yield GeojsonPointItem(
            properties=properties,
            lon_lat=lon_lat,
        )
