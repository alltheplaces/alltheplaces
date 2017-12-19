# -*- coding: utf-8 -*-
import scrapy
import json

from locations.items import GeojsonPointItem


class RossDressSpider(scrapy.Spider):
    name = "ross_dress"
    allowed_domains = ["hosted.where2getit.com"]
    start_urls = (
        'https://hosted.where2getit.com/rossdressforless/2014/ajax?&xml_request=<request><appkey>1F663E4E-1B64-11E5-B356-3DAF58203F82</appkey><formdata id="locatorsearch"><dataview>store_default</dataview><limit>99999</limit><geolocs><geoloc><longitude>-98.5795</longitude><latitude>39.8283</latitude></geoloc></geolocs><searchradius>4000|2500</searchradius><where><clientkey><eq></eq></clientkey><opendate><eq></eq></opendate><shopping_spree><eq></eq></shopping_spree></where></formdata></request>',
        'https://hosted.where2getit.com/rossdressforless/2014/ajax?&xml_request=<request><appkey>1F663E4E-1B64-11E5-B356-3DAF58203F82</appkey><formdata id="locatorsearch"><dataview>store_default</dataview><limit>99999</limit><geolocs><geoloc><longitude>-84.5947</longitude><latitude>40.6577</latitude></geoloc></geolocs><searchradius>4000|2500</searchradius><where><clientkey><eq></eq></clientkey><opendate><eq></eq></opendate><shopping_spree><eq></eq></shopping_spree></where></formdata></request>',
    )


    def store_hours(self, store_hours):
        day_groups = []
        this_day_group = None
        days = ('Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su')

        for day, hours in zip(days, store_hours):            
            hour_intervals = []
            (f_time, t_time) = hours.split('-')
            if len(f_time) > 0 and len(t_time)> 0:
                f_ampm = f_time[-2:]
                f_hr = f_time[:2]
                t_ampm = t_time[-2:]
                t_hr = t_time[:2]

                f_hr = int(f_hr)
                t_hr = int(t_hr)
                if f_ampm == 'PM':
                    f_hr += 12
                if f_ampm == 'AM' and f_hr == 12:
                    f_hr -= 12

                if t_ampm == 'PM':
                    t_hr += 12
                if t_ampm == 'AM' and t_hr == 12:
                    t_hr -= 12

                hour_intervals.append('{}:{}-{}:{}'.format(
                    f_hr,
                    f_time[3:5],
                    t_hr,
                    t_time[3:5],
                ))
            hours = ','.join(hour_intervals)
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
        data = response.xpath('//poi')

        for store in data:
            properties = {
                "ref": str(store.xpath('clientkey/text()').extract_first()),
                "name": store.xpath('name/text()').extract_first(),
                "website": store.xpath('website/text()').extract_first(),
                "addr_full": store.xpath('address1/text()').extract_first(),
                "city": store.xpath('city/text()').extract_first(),
                "state": store.xpath('state/text()').extract_first(),
                "postcode": store.xpath('postalcode/text()').extract_first(),
                "country": store.xpath('country/text()').extract_first(),
                "lon": float(store.xpath('longitude/text()').extract_first()),
                "lat": float(store.xpath('latitude/text()').extract_first()),
            }

            phone = store.xpath('phone/text()')
            if phone:
                properties['phone'] = phone.extract_first()

            hours = [store.xpath('monday/text()').extract_first(),
                           store.xpath('tuesday/text()').extract_first(),
                           store.xpath('wednesday/text()').extract_first(),
                           store.xpath('thursday/text()').extract_first(),
                           store.xpath('friday/text()').extract_first(),
                           store.xpath('saturday/text()').extract_first(),
                           store.xpath('sunday/text()').extract_first(),
                    ]
            if hours:
                properties['opening_hours'] = self.store_hours(hours)

            yield GeojsonPointItem(**properties)

        else:
            self.logger.info("No results")

