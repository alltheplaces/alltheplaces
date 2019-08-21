# -*- coding: utf-8 -*-
import scrapy
import json
import datetime
from locations.items import GeojsonPointItem


class TemplateSpider(scrapy.Spider):
    name = "department_veterans_affairs"
    allowed_domains = ["api.va.gov"]

    def start_requests(self):

        for i in range(1, 117):
            URL = 'https://api.va.gov/v0/facilities/va?address=United%%20States&bbox[]=-180&bbox[]=90&bbox[]=180&bbox[]=-90&type=all&page=%s' % i
            yield scrapy.Request(URL, callback=self.parse_info)


    def store_hours(self, store_hours):
        if not store_hours:
            return None
        if all([h == '' for h in store_hours.values()]):
            return None

        day_groups = []
        this_day_group = None
        for day in ('monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'):
            hours = store_hours.get(day)
            if not hours:
                continue

            hours = hours.replace(' - ', '-')
            hours = hours.replace(' ', '')

            if hours != "Closed":
                temp = hours.split('-')

                try:
                    try:
                        from_time = datetime.datetime.strptime(temp[0], '%I%M%p').strftime('%H:%M') + "-"
                        to_time = datetime.datetime.strptime(temp[1], '%I%M%p').strftime('%H:%M')
                    except:
                        from_time = datetime.datetime.strptime(temp[0], '%I:%M%p').strftime('%H:%M') + "-"
                        to_time = datetime.datetime.strptime(temp[1], '%I:%M%p').strftime('%H:%M')
                    hours = from_time + to_time
                except:
                    return None

            day_short = day[:2]
            day_short = day_short.title()

            if not this_day_group:
                this_day_group = dict(from_day=day_short, to_day=day_short, hours=hours)
            elif this_day_group['hours'] == hours:
                this_day_group['to_day'] = day_short
            elif this_day_group['hours'] != hours:
                day_groups.append(this_day_group)
                this_day_group = dict(from_day=day_short, to_day=day_short, hours=hours)

        day_groups.append(this_day_group)


        if len(day_groups) == 1:
            if day_groups['hours'] == 'Closed':
                pass
            else:
                opening_hours = day_groups[0]['hours']
                if opening_hours == '04:00-04:00':
                    opening_hours = '24/7'
        else:
            opening_hours = ''
            for day_group in day_groups:
                if day_group['from_day'] == day_group['to_day']:
                    if day_group['hours'] == 'Closed':
                        pass
                    else:
                        opening_hours += '{from_day} {hours}; '.format(**day_group)
                else:
                    if day_group['hours'] == 'Closed':
                        pass
                    else:
                        opening_hours += '{from_day}-{to_day} {hours}; '.format(**day_group)
            opening_hours = opening_hours[:-2]

        return opening_hours



    def parse_info(self, response):


        data = json.loads(response.body_as_unicode())

        data = data['data']


        for row in data:

            place_info = row['attributes']

            properties = {
                "ref": row['id'],
                "name": place_info['name'],
                "lat": place_info['lat'],
                "lon": place_info['long'],
                "addr_full": place_info['address']['physical']['address_1'],
                "city": place_info['address']['physical']['city'],
                "state": place_info['address']['physical']['state'],
                "country": 'US',
                "postcode": place_info['address']['physical']['zip'],
                "website": place_info['website'],
                "phone": place_info['phone']['main'],
                'extras':
                    {
                        'type': place_info["facility_type"]
                    }
            }

            hours = place_info.get('hours')
            try:
                hours = self.store_hours(hours)
                if hours:
                    properties['opening_hours'] = hours
            except:
                self.logger.exception("Couldn't process opening hours: %s", hours)

            yield GeojsonPointItem(**properties)






