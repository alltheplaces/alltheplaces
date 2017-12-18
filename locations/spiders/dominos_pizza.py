# -*- coding: utf-8 -*-
import scrapy
import json
import re

from locations.items import GeojsonPointItem


class DominosPizzaSpider(scrapy.Spider):
    name = "dominos_pizza"
    allowed_domains = ["dominos.com", "google.com"]
    start_urls = (
        'https://pizza.dominos.com/',
    )

    def store_hours(self, store_hours):
        opening_hours = ''
        for s in store_hours:  # loop by days
            clear_s = s.replace('</li>', '').replace('<li>', '').replace('</span>', '').replace('<span>', '')
            parts = re.search(r'(\D{3})(-(\D{3}))?\s*:\s*(\d{1,2})(:(\d{2}))?\s*(\D{2})\s*to\s*(\d{1,2})(:(\d{2}))?\s*(\D{2})',clear_s)
            if not parts:
                opening_hours += clear_s
                continue
            opening_hours += parts[1][:2]

            if parts[3]:
                opening_hours += '-'+parts[3][:2]

            if parts[7] == 'pm':
                opening_hours += ' '+str(int(parts[4])+12)
            else:
                opening_hours += ' '+parts[4]

            if parts[5]:
                opening_hours += parts[5]+'-'
            else:
                opening_hours += ':00-'

            if parts[11] == 'pm':
                opening_hours += str(int(parts[8])+12)
            else:
                opening_hours += parts[8]

            if parts[10]:
                opening_hours += parts[10]
            else:
                opening_hours += ':00'

            opening_hours += ';'

        return opening_hours.rstrip(';').strip()

    def phone_normalize(self, phone):
        r = re.search(r'\+?(\s+)*(\d{1})?(\s|\()*(\d{3})(\s+|\))*(\d{3})(\s+|-)?(\d{2})(\s+|-)?(\d{2})',phone)
        return ('('+r.group(4)+') '+r.group(6)+'-'+r.group(8)+'-'+r.group(10)) if r else phone

    def parse(self, response):  # high-level list of states
        states = response.xpath('//div[contains(.,"States")]/ul/li/a/@href')
        for state in states:
            yield scrapy.Request(response.urljoin(state.extract()), callback=self.parse_state)

    def parse_state(self, response):  # high-level list of states
        cities = response.xpath('//div[contains(.,"Cities")]/ul/li/a/@href')
        for city in cities:
            yield scrapy.Request(response.urljoin(city.extract()), callback=self.parse_city)

    def parse_city(self, response):  # high-level list of states
        this_place = json.loads(response.xpath('//script[@type="application/ld+json"]/text()').extract_first())['eligibleRegion']['address']['addressLocality']
        rows = response.xpath('//div[@class="col-xs-12"]')
        for row in rows:
            if row.xpath('./h2/text()').extract_first().find(this_place) != -1:
                places = row.xpath('./ul/li/a/@href')
                for place in places:
                    yield scrapy.Request(response.urljoin(place.extract()), callback=self.parse_place)

    def parse_place(self, response):
        data = json.loads(response.xpath('//script[@type="application/ld+json"]/text()').extract_first())
        time = response.xpath('//dl[@class="list-hours"]/ul/li').extract()
        yield GeojsonPointItem(
            lat=float(data['geo']['latitude']),
            lon=float(data['geo']['longitude']),
            phone=data['telephone'],
            website=response.url,
            ref=data['branchCode'],
            opening_hours=self.store_hours(time),
            addr_full=data['address']['streetAddress'],
            city=data['address']['addressRegion'],
            state=data['address']['addressRegion'],
            postcode=data['address']['postalCode'],
            country=data['address']['addressCountry'],
        )
