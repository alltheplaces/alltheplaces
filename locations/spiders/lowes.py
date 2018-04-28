# -*- coding: utf-8 -*-
import scrapy
from locations.items import GeojsonPointItem
import re
from urllib.parse import urlencode

class LowesSpider(scrapy.Spider):
    """" This spider scrapes Lowes store locations """
    name = "lowes"
    allowed_domains = ["www.lowes.com"]
    start_urls = ('https://www.lowes.com/Lowes-Stores',)
    download_delay = 1.5

    def extract_hours(self, hours_str):
        day_groups = []
        this_day_group = None

        hours = None
        for m in re.finditer(r"(\S*)_(\S*):'(\d{2})\.(\d{2})\S*'", hours_str):
            day, open_close, h, m = m.groups()
            day_short = day[:2]

            if open_close == 'Open':
                hours = '%s:%s' % (h, m)
                continue
            else:
                hours = hours + "-%s:%s" % (h, m)

            if not this_day_group:
                this_day_group = dict(from_day=day_short, to_day=day_short, hours=hours)
            elif this_day_group['hours'] == hours:
                this_day_group['to_day'] = day_short
            elif this_day_group['hours'] != hours:
                day_groups.append(this_day_group)
                this_day_group = dict(from_day=day_short, to_day=day_short, hours=hours)
            hours = ''
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

    def parse_store(self, response):
        js_content = response.xpath('normalize-space(//div[@class="store"]/script/text())').extract_first()
        match = re.search(r"country: '(\S*)', lat: (-?\d+\.\d+), lng: (-?\d+\.\d+), key: '(.*?)', storeHours: { (.*?) } };", js_content)
        if not match:
            return

        country, lat, lng, ref, hours_str = match.groups()

        properties = {
            'lat': float(lat),
            'lon': float(lng),
            'country': country,
            'ref': ref,
            'addr_full': response.xpath('normalize-space(//span[@itemprop="streetAddress"]/text())').extract_first(),
            'city': response.xpath('normalize-space(//span[@itemprop="addressLocality"]/text())').extract_first(),
            'state': response.xpath('normalize-space(//span[@itemprop="addressRegion"]/text())').extract_first(),
            'postcode': response.xpath('normalize-space(//span[@itemprop="postalCode"]/text())').extract_first(),
            'phone': response.xpath('normalize-space(//span[@itemprop="telephone"]/text())').extract_first(),
            'website': response.request.url,
            'opening_hours': self.extract_hours(hours_str),
        }

        yield GeojsonPointItem(**properties)

    def parse_state(self, response):
        city_urls = response.xpath('//div[@class="v-spacing-small"]/a/@href').extract()
        for path in city_urls:
            yield scrapy.Request(response.urljoin(path), callback=self.parse_store)

    def parse(self, response):
        urls = response.xpath('//li[@role="listitem"]/a/@href').extract()
        for path in urls:
            yield scrapy.Request(response.urljoin(path), callback=self.parse_state)
