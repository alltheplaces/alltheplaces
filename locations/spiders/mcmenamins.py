# -*- coding: utf-8 -*-
import scrapy
import json
import re

from locations.items import GeojsonPointItem

class McmenaminsSpider(scrapy.Spider):
    name = "mcmenamins"
    allowed_domains = ["mcmenamins.com","google.com"]
    start_urls = (
        'https://www.mcmenamins.com/eat-drink',
    )

    def store_hours(self, store_hours):
        day_groups = []
        this_day_group = None
        for line in store_hours:
            day = line['day'][0].upper()+line['day'][1].lower()

            if not line['intervals']:
                continue

            for period in line['intervals']:
                hours = '{0}:{1}-{2}:{3}'.format(
                    str(period['start'])[:2],
                    str(period['start'])[2:],
                    str(period['end'])[:2],
                    str(period['end'])[2:],
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

        if this_day_group:
            day_groups.append(this_day_group)

        opening_hours = ""
        if len(day_groups) == 1 and day_groups[0]['hours'] in ('00:00-23:59', '00:00-00:00'):
            opening_hours = '24/7'
        else:
            for day_group in day_groups:
                if day_group['from_day'] == day_group['to_day']:
                    opening_hours += '{from_day} {hours}; '.format(**day_group)
                elif day_group['from_day'] == 'Mo' and day_group['to_day'] == 'Su':
                    opening_hours += '{hours}; '.format(**day_group)
                else:
                    opening_hours += '{from_day}-{to_day} {hours}; '.format(**day_group)
            opening_hours = opening_hours[:-2]

        return opening_hours

    def phone_normalize(self, phone):
        r=re.search(r'\+?(\s+)*(\d{1})?(\s|\()*(\d{3})(\s+|\))*(\d{3})(\s+|-)?(\d{2})(\s+|-)?(\d{2})',phone)
        return ('('+r.group(4)+') '+r.group(6)+'-'+r.group(8)+'-'+r.group(10)) if r else phone

    def parse(self, response): #high-level list of states
        shops = response.xpath('//div[@id="MainContent_eatDrinkLocations"]/div[contains(@class,"all")]')
        i=1
        for path in shops:
            yield scrapy.Request(response.urljoin(path.xpath('.//div/div[@class="tm-panel-titlebg"]/a/@href').extract_first()), callback=self.parse_store, meta={
                   'ref':path.xpath('.//@id').extract_first(),
                    })

    def parse_store(self, response):
        google_pos=response.xpath('//div[@class="mcm-logo-address"]')[0].xpath('.//a[contains(@href,"maps.google")]/@href')[0].extract()
        address_full=response.xpath('//div[@class="mcm-logo-address"]')[0].xpath('.//a/p/text()').extract_first()
        address_parts=re.match(r"(.{3,}),\s?(.{3,}),\s?(\w{2}) (\d{5})",address_full)
        yield scrapy.Request(google_pos, callback=self.google_maps, meta={
                'ref':response.meta.get('ref'),
                'website':response.url,
                'addr_full':address_parts[1].strip(),
                'city':address_parts[2].strip(),
                'state':address_parts[3].strip(),
                'postcode':address_parts[4].strip(),
                'phone':self.phone_normalize(response.xpath('//div[@class="mcm-logo-address"]')[0].xpath('.//ul/li/a/@href').extract_first()),
                })

    def google_maps(self, response):
        sc=response.xpath('//script[contains(.,"cacheResponse([")]').extract_first()
        latlon=json.loads(re.search(r'cacheResponse\((.*)\);',sc)[1])[8][0][2]
        yield GeojsonPointItem(
            lat=float(latlon[0]),
            lon=float(latlon[1]),
            phone=response.meta.get('phone'),
            website=response.meta.get('website'),
            ref=response.meta.get('ref'),
            opening_hours='',
            addr_full=response.meta.get('addr_full'),
            city=response.meta.get('city'),
            state=response.meta.get('state'),
            postcode=response.meta.get('postcode'),
            country='US',
        )
