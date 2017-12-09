# -*- coding: utf-8 -*-
import scrapy
import re

from locations.items import GeojsonPointItem


class SafewaySpider(scrapy.Spider):
    name = "safeway"
    allowed_domains = ['safeway.com']
    start_urls = (
        'https://local.safeway.com/sitemap.xml',
    )

    def store_hours(self, store_hours):
        day_groups = []
        this_day_group = None
        for line in store_hours:
            # Applebees always seems to have a single dow
            # in each opening hours object
            day = line['day'][0][:2]

            match = re.search(r'^(\d{1,2}):(\d{2})$', line['start'])
            (f_hr, f_min) = match.groups()
            match = re.search(r'^(\d{1,2}):(\d{2})$', line['end'])
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


    def parse(self, response):
        response.selector.remove_namespaces()
        city_urls = response.xpath('//*/*[@href]').extract()
        for path in city_urls:
            locationURL = re.compile(r'https://local.safeway.com/(safeway/|\S+)/\S+/\S+')
            if not re.search(locationURL, path):
                pass
            else:
                path = re.search(locationURL, path)[0].strip('"/>')
                yield scrapy.Request(
                    path.strip(),
                    callback=self.parse_store,
                )

    def parse_store(self, response):

        properties = {
            'name': response.xpath('/html/body/main/div[2]/div/section[1]/div[2]/div[1]/h1/span/span[2]/text()').extract(),
            'website': response.request.url,
            'ref': response.xpath('/html/body/main/div[2]/div/section[1]/div[2]/div[1]/h1/span/span[2]/text()').extract(),
#            'opening_hours': self.store_hours(response.xpath('/html/body/main/div[2]/div/section[1]/div[2]/div[2]/div[1]/div[2]/div[@data-days]').extract()[0].split("data-days=\'")[1].split("\'")[0]),
            'addr_full': response.xpath('/html/body/main/div[2]/div/section[1]/div[2]/div[1]/div[1]/address/span[1]/span/text()').extract(),
            'city': response.xpath('/html/body/main/div[2]/div/section[1]/div[2]/div[1]/div[1]/address/span[2]/span[1]/text()').extract(),
            'state': response.xpath('/html/body/main/div[2]/div/section[1]/div[2]/div[1]/div[1]/address/abbr[1]/text()').extract(),
            'postcode': response.xpath('/html/body/main/div[2]/div/section[1]/div[2]/div[1]/div[1]/address/span[3]/text()').extract(),
             'lon': float(response.xpath('//*[@id="js-map-config-dir-map-desktop"]').extract()[0].split('"latitude":')[1].split(',')[0]),
             'lat': float(response.xpath('//*[@id="js-map-config-dir-map-desktop"]').extract()[0].split('"longitude":')[1].split(',')[0]),
        }

        yield GeojsonPointItem(**properties)