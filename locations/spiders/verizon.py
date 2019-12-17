# -*- coding: utf-8 -*-
import scrapy
import json
import re

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class VerizonSpider(scrapy.Spider):
    name = "verizon"
    brand = "Verizon"
    allowed_domains = ["www.verizonwireless.com"]
    start_urls = (
        'https://www.verizonwireless.com/sitemap_storelocator.xml',
    )
    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36',
    }

    def parse_hours(self, store_hours):
        opening_hours = OpeningHours()
        for store_day in store_hours['dayOfWeek']:
            if store_day.lower() == 'closed':
                continue
            else:
                day, open_close = store_day.split('-')
                day = day.strip()[:2]
                open_time = ' '.join(open_close.strip().split(' ', 2)[0:2])
                if open_time.split(' ')[0].lower() == 'closed':
                    continue
                elif open_time.split(' ')[0].lower() == 'null':
                    continue
                else:
                    if open_close.strip().count(' ') == 1:
                        open_time, close_time = open_time.split(' ')
                        opening_hours.add_range(day=day,
                                                open_time=open_time,
                                                close_time=close_time,
                                                time_format='%I:%M%p'
                                                )
                    elif open_close.strip().count(' ') == 2:
                        open_time = open_close.strip().split(' ')[0]
                        close_time = ''.join(open_close.strip().split(' ')[1:3])
                        opening_hours.add_range(day=day,
                                                open_time=open_time,
                                                close_time=close_time,
                                                time_format='%I:%M%p'
                                                )
                    else:
                        close_time = open_close.strip().split(' ', 2)[2]
                        opening_hours.add_range(day=day,
                                                open_time=open_time,
                                                close_time=close_time,
                                                time_format='%I:%M %p'
                                                )

        return opening_hours.as_opening_hours()

    def parse(self, response):
        response.selector.remove_namespaces()
        urls = response.xpath('//url/loc/text()').extract()

        for url in urls:
            yield scrapy.Request(url, callback=self.parse_store)

    def parse_store(self, response):
        script = response.xpath('//script[contains(text(), "storeJSON")]/text()').extract_first()
        store_data = json.loads(re.search(r'var storeJSON = (.*);', script).group(1))

        properties = {
                'name': store_data["storeName"],
                'ref': store_data["storeNumber"],
                'addr_full': store_data["address"]["streetAddress"],
                'city': store_data["address"]["addressLocality"],
                'state': store_data["address"]["addressRegion"],
                'postcode': store_data["address"]["postalCode"],
                'country': store_data["address"]["addressCountry"],
                'phone': store_data.get("telephone"),
                'website': store_data.get("url") or response.url,
                'lat': store_data["geo"].get("latitude"),
                'lon': store_data["geo"].get("longitude"),
                'extras': {
                    'business_name': store_data.get('posStoreDetail').get('businessName'),
                    'retail_id': store_data.get('retailId'),
                    'store_type': store_data.get('posStoreDetail').get('storeType'),
                    'store_type_note': store_data.get('typeOfStore')
                }
            }

        hours = self.parse_hours(store_data.get("openingHoursSpecification"))
        if hours:
            properties["opening_hours"] = hours

        yield GeojsonPointItem(**properties)
