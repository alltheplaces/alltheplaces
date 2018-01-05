# -*- coding: utf-8 -*-
import scrapy
from locations.items import GeojsonPointItem
import json

day_formats = {
    "Monday": "Mo",
    "Tuesday": "Tu",
    "Wednesday": "We",
    "Thursday": "Th",
    "Friday": "Fr",
    "Saturday": "Sa",
    "Sunday": "Su",
}

class TheCheeseFactorySpider(scrapy.Spider):

    name = "the_cheese_factory"
    allowed_domains = ["locations.thecheesecakefactory.com"]
    start_urls = (
        "http://locations.thecheesecakefactory.com",
    )

    def parse(self, response):
        elements = response.xpath('//a[@linktrack]/@href').extract()

        if len(elements) > 0:
            for index, link in enumerate(elements):
                yield scrapy.Request(
                    link,
                    callback=self.parse,
                )
        else:
            self.parse_location(response)

    def parse_location(self, response):

        properties = {
            'addr_full': response.xpath('//div[@itemprop="address"]/div[@itemprop="address"]/p//text()').extract(),
        }

        scripts = response.xpath('//script[@type="application/ld+json"]/text()').extract()

        for script in scripts:

            try:
                json_string = json.loads(script.strip())
            except:
                json_string = json.loads(script.strip().rstrip('}'))

            if 'name' not in json_string:
                continue

            properties['ref'] = json_string['name']
            properties['lat'] = float(json_string['geo']['latitude'])
            properties['lon'] = float(json_string['geo']['longitude'])
            properties['phone'] = json_string['telephone']
            properties['country'] = json_string['address']['addressCountry']
            properties['state'] = json_string['address']['addressRegion']
            properties['city'] = json_string['address']['addressLocality']
            properties['postcode'] = json_string['address']['postalCode']
            properties['opening_hours'] = self.parse_opening_hours(json_string['openingHoursSpecification'])

            yield GeojsonPointItem(**properties)

    def parse_opening_hours(self, data):

        day_groups = []
        this_day_group = None

        for day in data:
            hours = '%s-%s' % (day['opens'], day['closes'])
            today = day_formats[day['dayOfWeek'][0]]

            if not this_day_group:
                this_day_group = {
                    'from_day': today,
                    'to_day': today,
                    'hours': hours,
                }
            elif this_day_group['hours'] != hours:
                day_groups.append(this_day_group)
                this_day_group = {
                    'from_day': today,
                    'to_day': today,
                    'hours': hours,
                }
            elif this_day_group['hours'] == hours:
                this_day_group['to_day'] = today

        day_groups.append(this_day_group)

        opening_hours = ''

        for day_group in day_groups:
            if day_group['from_day'] == day_group['to_day']:
                opening_hours += '{from_day} {hours}; '.format(**day_group)
            elif day_group['from_day'] == 'Su' and day_group['to_day'] == 'Sa':
                opening_hours += '{hours}; '.format(**day_group)
            else:
                opening_hours += '{from_day}-{to_day} {hours}; '.format(**day_group)

        opening_hours = opening_hours[:-2]

        return opening_hours
