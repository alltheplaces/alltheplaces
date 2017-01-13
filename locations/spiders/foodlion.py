# -*- coding: utf-8 -*-
import scrapy
import json
import re

from locations.items import GeojsonPointItem

class FoodLionSpider(scrapy.Spider):
    name = "foodlion"
    allowed_domains = ["www.foodlion.com"]
    start_urls = (
        'https://www.foodlion.com/stores/_jcr_content/mainParsys/storelocator.stores.json?lat=37.8&lng=-79.5&distance=5000&pharmacyFilter=false',
    )

    def store_hours(self, store_hours):
        day_groups = []
        for line in store_hours:
            this_day_group = dict()
            (front, rest) = line.split(': ')

            days = front.split('-')
            if days:
                this_day_group['from_day'] = days[0][:2]
                this_day_group['to_day'] = days[0][:2]
            if len(days) == 2:
                this_day_group['to_day'] = days[1][:2]

            if rest == 'Closed':
                continue
            elif rest:
                match = re.search(r'^(\d+):(\d+) (am|pm)-(\d+):(\d+) (am|pm)$', rest)
                if match:
                    (f_hr, f_min, f_ampm, t_hr, t_min, t_ampm) = match.groups()
                    if f_ampm == 'pm':
                        f_hr = int(f_hr) + 12
                    if t_ampm == 'pm':
                        t_hr = int(t_hr) + 12

                    this_day_group['hours'] = "{:02d}:{:02d}-{:02d}:{:02d}".format(
                        int(f_hr),
                        int(f_min),
                        int(t_hr),
                        int(t_min),
                    )
                elif rest == 'Open 24 Hours':
                    this_day_group['hours'] = '24/7'

                day_groups.append(this_day_group)

        opening_hours = ""
        if len(day_groups) == 1 and day_groups[0]['hours'] == '24/7':
            opening_hours = '24/7'
        else:
            for day_group in day_groups:
                if day_group['from_day'] == day_group['to_day']:
                    opening_hours += '{from_day} {hours}; '.format(**day_group)
                elif day_group['from_day'] == 'Su' and day_group['to_day'] == 'Sa':
                    opening_hours += '{hours}; '.format(**day_group)
                else:
                    opening_hours += '{from_day}-{to_day} {hours}; '.format(**day_group)
            opening_hours = opening_hours[:-2]

        return opening_hours

    def address(self, address):
        if not address:
            return None

        (num, rest) = address['address'].split(' ', 1)
        addr_tags = {
            "addr:housenumber": num.strip(),
            "addr:street": rest.strip(),
            "addr:city": address['city'],
            "addr:state": address['state'],
            "addr:postcode": address['zip'],
        }

        return addr_tags

    def parse(self, response):
        data = json.loads(response.body_as_unicode())

        for store in data:
            properties = {
                "phone": store['phoneNumber'],
                "ref": str(store['storeId']),
                "name": store['title'],
                "opening_hours": self.store_hours(store['hours']),
                "website": "https://www.foodlion.com{}".format(store['href']),
            }

            address = self.address(store)
            if address:
                properties.update(address)

            lon_lat = [
                float(store['lng']),
                float(store['lat']),
            ]

            yield GeojsonPointItem(
                properties=properties,
                lon_lat=lon_lat,
            )

        else:
            self.logger.info("No results")
