import scrapy
import re

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


DAY_MAPPING = {
    'Montag': 'Mo',
    'Dienstag': 'Tu',
    'Mittwoch': 'We',
    'Donnerstag': 'Th',
    'Freitag': 'Fr',
    'Samstag': 'Sa',
    'Sonntag': 'Su'
}


class VRBankSpider(scrapy.Spider):
    name = "vr_bank"
    allowed_domains = ["www.vr.de"]
    start_urls = ['https://www.vr.de/service/filialen-a-z/a.html']

    def start_requests(self):
        index = response.xpath('//div[has-class("module module-linklist ym-clearfix")]/ul/li/a/@href').getall()

        for page in index:
            yield scrapy.Request(
                url=page,
                callback=self.parse
            )

    def process_hours(self, store_hours):
        opening_hours = OpeningHours()

        day = time = open_time = close_time = ""

        if store_hours is None:
            return

        for hour in store_hours:
            hour = hour.replace(": ", "#")
            try:
                day, time = hour.split("#")
            except Exception:
                pass

            if time and day in DAY_MAPPING.keys():
                time = time.replace("24:00", "00:00")
                tms = []
                if 'und' in time:
                    tms = [tm.strip() for tm in time.split('und')]
                else:
                    tms.append(time)

                for tm in tms:
                    try:
                        open_time, close_time = [t.strip() for t in tm.replace('Uhr', '').strip().split("-")]
                    except Exception:
                        pass

                    if open_time and close_time and day:
                        opening_hours.add_range(
                            day=DAY_MAPPING[day],
                            open_time=open_time,
                            close_time=close_time,
                            time_format='%H:%M'
                        )
                    else:
                        continue

        return opening_hours.as_opening_hours()

    def parse_details(self, response):
        if response.status == 403:
            yield scrapy.Request(
                url=response.meta.get('url'),
                callback=self.parse_details,
                meta={'url': response.meta.get('url')}
            )

        name = street = zip = city = phone = website = latitude = longitude = ""

        try:
            name = response.xpath('//h1[@itemprop="name"]/text()').get()
            street = response.xpath('//span[@itemprop="streetAddress"]/text()').get()
            zip = response.xpath('//span[@itemprop="postalCode"]/text()').get()
            city = response.xpath('//span[@itemprop="addressLocality"]/text()').get()
            phone = response.xpath('//li[@itemprop="telephone"]/a/span/text()').get()
            website = response.xpath('//li[@itemprop="url"]/a/span/text()').get()
        except Exception:
            print("Error: contact details not found for url: {}".format(response.meta.get('url')))

        try:
            m = re.search(r'lat&quot;:([-+]?[0-9]*\.?[0-9]*)', response.text)
            if m:
                latitude = m.group(1)
        except Exception:
            print("Error: latitude not found for url: {}".format(response.meta.get('url')))

        try:
            m = re.search(r'lng&quot;:([-+]?[0-9]*\.?[0-9]*)', response.text)
            if m:
                longitude = m.group(1)
        except Exception:
            print("Error: longitude not found for url: {}".format(response.meta.get('url')))

        try:
            hours = response.xpath('//p[@itemprop="openingHoursSpecification"]/text()').getall()
        except Exception:
            print("Error: working hours information not found for url: {}".format(response.meta.get('url')))

        properties = {
            'ref': response.meta.get('url'),
            'name': name,
            'city': city,
            'street': street,
            'postcode': zip,
            'phone': phone,
            'website': website,
            'lat': latitude,
            'lon': longitude
        }

        if hours:
            properties['opening_hours'] = self.process_hours(hours)

        yield GeojsonPointItem(**properties)

    def parse(self, response):
        list = response.xpath('//div[has-class("module module-teaserlist ym-clearfix")]/div/a/@href').getall()
        for item in list:
            yield scrapy.Request(
                url=item,
                callback=self.parse_details,
                meta={'url': item}
            )

