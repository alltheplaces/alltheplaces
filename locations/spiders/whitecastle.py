# -*- coding: utf-8 -*-
import scrapy
import json
import re

from locations.items import GeojsonPointItem

class WhiteCastleSpider(scrapy.Spider):
    name = "whitecastle"
    allowed_domains = ["www.whitecastle.com"]
    timeregex = re.compile('^([0-9:]+)(AM|PM)$')
    start_urls = (
        'https://www.whitecastle.com/api/location/search?form=%7B%22origin%22%3A%7B%22latitude%22%3A40.75368539999999%2C%22longitude%22%3A-73.9991637%7D%2C%22count%22%3A9999999%2C%22skip%22%3A0%2C%22targets%22%3A%5B%22Castle%22%5D%7D',
    )

    def normalize_time(self, time_str):
        time, ampm = self.timeregex.search(time_str).groups()
        hour, minute = time.split(':')

        hour = int(hour)
        if ampm == 'PM' and hour != 12:
            hour = hour + 12
        return '%02d:%s' % (hour, minute)

    def normalize_dayrange(self, dayrange):
        replacements = [
            ["Monday", "Mo"],
            ["Tuesday", "Tu"],
            ["Wednesday", "We"],
            ["Thursday", "Th"],
            ["Friday", "Fr"],
            ["Saturday", "Sa"],
            ["Sunday", "Su"],
            ["Mon", "Mo"],
            ["Tue", "Tu"],
            ["Wed", "We"],
            ["Thu", "Th"],
            ["Fri", "Fr"],
            ["Sat", "Sa"],
            ["Sun", "Su"],
            [" - ", "-"]
        ]
        for r in replacements:
            dayrange = dayrange.replace(r[0], r[1])
        return dayrange

    def store_hours(self, timetable):
        if (len(timetable) == 1):
            hours = timetable[0]
            if (hours['dayOfWeek'] == 'Sun - Sat') and \
               ('24 Hours' in hours['formattedTitles'][0]):
                return '24/7'

        opening_hours = ""
        for time in timetable:
            dayrange = time['dayOfWeek']
            dayrange = self.normalize_dayrange(dayrange)
            times = time['formattedTitles'][0]

            if ('24 Hours' in times):
                hours = "00:00-24:00"
            else:
                opentime, closetime = times.split(' - ')
                hours = '{}-{}'.format(
                    self.normalize_time(opentime),
                    self.normalize_time(closetime),
                )
            opening_hours += '{dayrange} {hours}; '.format(dayrange=dayrange, hours=hours)

        return opening_hours[:-2]

    def parse(self, response):
        data = json.loads(response.body_as_unicode())

        for store in data:
            unp = {
                "ref": store.get('id'),
                "name": store.get('name'),
                "addr_full": store.get('address'),
                "city": store.get('city'),
                "state": store.get('state'),
                "postcode": store.get('zip'),
                "phone": store.get('telephone'),
            }
            if store.get('url'):
                unp['website'] = 'https://www.whitecastle.com' + store.get('url')

            if store.get('latitude'): unp['lon'] = float(store.get('latitude'))
            if store.get('longitude'): unp['lat'] = float(store.get('longitude'))

            if store.get('timetable'):
                opening_hours = self.store_hours(store.get('timetable'))
                if opening_hours: unp['opening_hours'] = opening_hours

            properties = {}
            for key in unp:
                if unp[key]:
                    if isinstance(unp[key], str):
                        properties[key] = unp[key].strip()
                    else: 
                        properties[key] = unp[key]

            yield GeojsonPointItem(**properties)

