# -*- coding: utf-8 -*-
import scrapy
import json
import re

from locations.items import GeojsonPointItem


class DollarTreeSpider(scrapy.Spider):
    name = "dollartree"
    allowed_domains = ["locations.dollartree.com"]
    start_urls = (
        'https://locations.dollartree.com',
    )

    def store_hours(self, store_hours):
        day_groups = []
        this_day_group = None
        for line in store_hours:
            # Applebees always seems to have a single dow
            # in each opening hours object
            day = line['dayOfWeek'][0][:2]

            match = re.search(r'^(\d{1,2}):(\d{2})$', line['opens'])
            (f_hr, f_min) = match.groups()
            match = re.search(r'^(\d{1,2}):(\d{2})$', line['closes'])
            (t_hr, t_min) = match.groups()

            f_hr = int(f_hr)
            t_hr = int(t_hr)


            hours = '{:02d}:{}-{:02d}:{}'.format(
                f_hr,
                f_min,
                t_hr,
                t_min,
            )

            if not this_day_group:
                this_day_group = {
                    'from_day': day,
                    'to_day': day,
                    'hours': hours
                }
            elif this_day_group['hours'] != hours:
                day_groups.append(this_day_group)
                this_day_group = {
                    'from_day': day,
                    'to_day': day,
                    'hours': hours
                }
            elif this_day_group['hours'] == hours:
                this_day_group['to_day'] = day

        day_groups.append(this_day_group)

        opening_hours = ""
        if len(day_groups) == 1 and day_groups[0]['hours'] in ('00:00-23:59', '00:00-00:00'):
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

        addr_tags = {
            "addr:full": address['streetAddress'],
            "addr:city": address['addressLocality'],
            "addr:state": address['addressRegion'],
            "addr:postcode": address['postalCode'],
            "addr:country": address['addressCountry'],
        }

        return addr_tags

    def parse(self, response):
        urls = response.xpath('///div[2]/table//@href')
        for path in urls:
            yield scrapy.Request(response.urljoin(path.extract()))

        store_urls = response.xpath('//*[@id="storeinfo_div"]/a//@href')
        if store_urls:
            for store_url in store_urls:
                yield scrapy.Request(response.urljoin(store_url.extract()), callback=self.parse_store)

    def parse_store(self, response):
        json_data = response.xpath('//head/script[@type="application/ld+json"]/text()')[1].extract()
        json_data = json_data.replace('// if the location file does not have the hours separated into open/close for each day, remove the below section', '')
        data = json.loads(json_data)

        properties = {
            'phone': data['telephone'],
            'website': response.xpath('//head/link[@rel="canonical"]/@href')[0].extract(),
            'ref': data['@id'],
            'opening_hours': self.store_hours(data['openingHoursSpecification'])
        }

        address = self.address(data['address'])
        if address:
            properties.update(address)

        lon_lat = [
            float(data['geo']['longitude']),
            float(data['geo']['latitude']),
        ]

        yield GeojsonPointItem(
            properties=properties,
            lon_lat=lon_lat,
        )