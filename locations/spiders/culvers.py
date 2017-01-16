# -*- coding: utf-8 -*-
import scrapy
import json
import re

from locations.items import GeojsonPointItem

class CulversSpider(scrapy.Spider):
    name = "culvers"
    allowed_domains = ["hosted.where2getit.com"]
    start_urls = (
        'http://hosted.where2getit.com/culvers/2015/ajax?&xml_request=%3Crequest%3E%3Cappkey%3E1099682E-D719-11E6-A0C4-347BDEB8F1E5%3C%2Fappkey%3E%3Cformdata+id%3D%22locatorsearch%22%3E%3Cdataview%3Estore_default%3C%2Fdataview%3E%3Climit%3E250%3C%2Flimit%3E%3Cstateonly%3E1%3C%2Fstateonly%3E%3Cgeolocs%3E%3Cgeoloc%3E%3Caddressline%3E54701%3C%2Faddressline%3E%3Ccountry%3E%3C%2Fcountry%3E%3C%2Fgeoloc%3E%3C%2Fgeolocs%3E%3Csearchradius%3E1000%3C%2Fsearchradius%3E%3C%2Fformdata%3E%3C%2Frequest%3E',
    )

    def store_hours(self, store_hours):
        day_groups = []
        days = ('Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su')
        this_day_group = dict()
        for day, hours in zip(days, store_hours):
            hours = '{}:{}-{}:{}'.format(
                hours[0][0:2],
                hours[0][2:4],
                hours[1][0:2],
                hours[1][2:4],
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

    def address(self, store):
        addr_tags = {
            "addr:full": store.xpath('address1/text()')[0].extract(),
            "addr:city": store.xpath('city/text()')[0].extract(),
            "addr:state": store.xpath('state/text()')[0].extract(),
            "addr:postcode": store.xpath('postalcode/text()')[0].extract(),
            "addr:country": store.xpath('country/text()')[0].extract(),
        }

        return addr_tags

    def parse(self, response):
        data = response.xpath('//poi')

        for store in data:
            properties = {
                "ref": str(store.xpath('number/text()')[0].extract()),
                "name": store.xpath('name/text()')[0].extract(),
                "opening_hours": self.store_hours(json.loads(store.xpath('bho/text()')[0].extract())),
                "website": store.xpath('url/text()')[0].extract(),
            }

            phone = store.xpath('phone/text()')
            if phone:
                properties['phone'] = phone[0].extract()

            address = self.address(store)
            if address:
                properties.update(address)

            lon_lat = [
                float(store.xpath('longitude/text()')[0].extract()),
                float(store.xpath('latitude/text()')[0].extract()),
            ]

            yield GeojsonPointItem(
                properties=properties,
                lon_lat=lon_lat,
            )

        else:
            self.logger.info("No results")
