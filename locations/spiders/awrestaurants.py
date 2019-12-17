# -*- coding: utf-8 -*-
import scrapy
import re

from locations.items import GeojsonPointItem

DETAIL_URL = 'https://www.awrestaurants.com/changeloc.php?zipcode={zipcode}'
HEADERS = {
           'Accept-Language': 'en-US,en;q=0.8,ru;q=0.6',
           'Host': 'www.awrestaurants.com',
           'Accept-Encoding': 'gzip, deflate, br',
           'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
           'Connection': 'keep-alive',
           'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36',
           }


class AwrestaurantsSpider(scrapy.Spider):
    name = "awrestaurants"
    item_attributes = { 'brand': "A&W Restaurants" }
    allowed_domains = ["www.awrestaurants.com"]
    start_urls = (
        'https://www.awrestaurants.com/locations?zipcode=67301',
    )

    def normalize_time(self, time_str):
        match = re.search(u'(.*) (am|a.m|pm|noon|p.m) \u2013 (.*) (am|a.m||pm|noon|p.m)', time_str)
        h1, am_pm1, h2, am_pm2 = match.groups()
        h1 = h1.split(':')
        h2 = h2.split(':')

        return '%02d:%02d-%02d:%02d' % (
            int(h1[0]) + 12 if am_pm1 == u'pm' or am_pm1 == u'noon' or am_pm1 == u'p.m' else int(h1[0]),
            int(h1[1]) if len(h1) > 1 else 0,
            int(h2[0]) + 12 if am_pm2 == u'pm' or am_pm2 == u'noon' or am_pm2 == u'p.m' else int(h2[0]),
            int(h2[1]) if len(h2) > 1 else 0,
        )

    def store_hours(self, content):
        store_hours = content[2].split('\r\n')

        opening_hours = []

        for day_info in store_hours:
            match = re.match(r'^(\w+)-?\.?([A-Za-z]*):\.? *(\d{1,2}):(\d{2}) ?(am|AM|pm|PM) *- +(\d{1,2}):(\d{2}) ?(am|AM|pm|PM)$', day_info)

            if day_info.lower().find('close') > -1:
                continue

            if not match:
                self.logger.warn("Couldn't match hours: %s", day_info)
                continue

            try:
                start_d, end_d, fr_hr,fr_min,fr_ampm, to_hr, to_min, to_ampm = match.groups()
            except ValueError:
                self.logger.warn("Couldn't match hours: %s", day_info)
                raise

            day_from = start_d[:2]
            day_to = end_d[:2]

            if day_from != day_to:
                day_str = '{}-{}'.format(day_from, day_to)
            else:
                day_str = '{}'.format(day_from)

            day_hours = '%s %02d:%02d-%02d:%02d' % (
                day_str,
                int(fr_hr) + 12 if fr_ampm == 'pm' else int(fr_hr),
                int(fr_min),
                int(to_hr) + 12 if to_ampm == 'pm' else int(to_hr),
                int(to_min),
            )

            opening_hours.append(day_hours.strip())

        return '; '.join(opening_hours)

    def parse(self, response):
        stores = response.xpath("//ul[@class='locations-list']//li[@class='location-entity']")

        for store in stores:
            address_full = store.xpath('form/button/div/div[contains(@class, "location-address")]/text()')[0].extract()
            city_state = store.xpath('form/button/div/span[contains(@class, "location-city")]/text()')[0].extract()
            phone = store.xpath('form/button/div/span[contains(@class, "location-phone")]/text()')[0].extract()
            zipcode_param = store.xpath('form/input[@id="zipcode"]/@value')[0].extract()
            match = re.search('([\w\s]+),\s(\w+)\s(\w+)', city_state)
            city, state, postcode = match.groups()
            url = DETAIL_URL.format(zipcode=zipcode_param)

            props = {
                'website': url,
                'addr_full': address_full,
                'city': city,
                'state': state,
                'postcode': postcode,
                'phone': phone,
                'ref': city + ', ' + postcode,
            }

            yield scrapy.http.FormRequest(url= url, dont_filter=True, method='POST', meta = {'product': props},
                                           headers=HEADERS, callback=self.parse_detail_product)

    def parse_detail_product(self, response):
        product = response.meta.get('product')

        try:
            hours_section = response.xpath('//section[@class="mode"]/text()').extract()
            if len(hours_section) == 3:
                opening_hours = self.store_hours(hours_section)
                product['opening_hours'] = opening_hours
        except Exception as err:
            self.logger.warn("Couldn't find opening hours")

        yield GeojsonPointItem(**product)

    def _clean_text(self, text):
        return re.sub("[\r\n\t]", "", text).strip()
