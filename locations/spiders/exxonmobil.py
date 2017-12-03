# -*- coding: utf-8 -*-
import scrapy

from locations.items import GeojsonPointItem


class ExxonMobilSpider(scrapy.Spider):
    name = "exxonmobil"
    allowed_domains = ["www.exxonmobilstations.com"]
    start_urls = (
        'http://www.exxonmobilstations.com/station-locations',
    )

    def store_hours(self, store_hours):
        day_groups = []
        hour_iter = iter(store_hours)
        this_day_group = None

        while True:
            try:
                day_elem = hour_iter.next()
            except StopIteration:
                break
            start_elem = hour_iter.next()
            end_elem = hour_iter.next()

            day = day_elem.xpath('@content').extract_first()[:2]
            start_time = start_elem.xpath('@content').extract_first()[:5]
            end_time = end_elem.xpath('@content').extract_first()[:5]

            hours = '{}-{}'.format(start_time, end_time)

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
            "addr_full": address['business:contact_data:street_address'],
            "city": address['business:contact_data:locality'],
            "state": address['business:contact_data:region'],
            "postcode": address['business:contact_data:postal_code'],
        }

        return addr_tags

    def parse(self, response):
        # This will spider through all the country and regional pages and get us to the individual store pages
        region_urls = response.xpath('//a[@class="sitemap_link sitemap_bar"]/@href').extract()
        for url in region_urls:
            yield scrapy.Request(url)

        if response.xpath('//head/meta[@property="og:type"][@content="website"]'):
            return

        # When we get to an individual store page the above for loop won't yield anything
        # so at this point we're processing an individual store page.
        contact_props = response.xpath('//head/meta[starts-with(@property, "business:contact_data:")]')
        contact_info = {}
        for ele in contact_props:
            contact_info[ele.xpath('@property').extract_first()] = ele.xpath('@content').extract_first()

        properties = {
            'phone': contact_info['business:contact_data:phone_number']
        }

        address = self.address(contact_info)
        if address:
            properties.update(address)

        opening_hour_props = response.xpath('//head/meta[starts-with(@property, "business:hours:")]')
        properties['opening_hours'] = self.store_hours(opening_hour_props)

        url = response.xpath('//head/link[@rel="canonical"]/@href').extract_first()
        properties['website'] = url

        name = response.xpath('//span[@itemprop="legalName"]/text()').extract_first()
        properties['name'] = name

        ref = response.url.rsplit('/', 1)[1].split('-', 1)[0]
        properties['ref'] = ref

        ll = response.xpath('//div[@itemtype="http://schema.org/GeoCoordinates"]')
        properties['lon'] = float(ll.xpath('//meta[@itemprop="longitude"]/@content').extract_first()),
        properties['lat'] = float(ll.xpath('//meta[@itemprop="latitude"]/@content').extract_first()),

        yield GeojsonPointItem(**properties)
