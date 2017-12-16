import scrapy
import re
import json
from locations.items import GeojsonPointItem

DAY_MAPPING = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']


class AceHardwareSpider(scrapy.Spider):
    name = "ace_hardware"
    allowed_domains = ["www.acehardware.com"]
    download_delay = 0.5
    start_urls = (
        'http://www.acehardware.com/acestoresitemap.xml',
    )

    def parse_hours(self, lis):
        days = []
        for day in DAY_MAPPING:
            if 'openingTime'+day in lis and 'closingTime'+day in lis:
                open_time = str(lis['openingTime'+day]).zfill(4)
                close_time = str(lis['closingTime'+day]).zfill(4)
                days.append("%s %s:%s-%s:%s" % (
                    day[:2],
                    open_time[0:2],
                    open_time[2:],
                    close_time[0:2],
                    close_time[2:],
                ))
        return '; '.join(days)

    def parse_stores(self, response):
        ref = response.meta['id']
        json_data = json.loads(response.body_as_unicode())

        if 'address1' not in json_data:
            return

        properties = {
            'addr_full': json_data['address1'],
            'phone': json_data['phoneNumber'],
            'city': json_data['city'],
            'state': json_data['stateCode'],
            'postcode': json_data['postalCode'],
            'ref': ref,
            'website': "http://www.acehardware.com/mystore/index.jsp?store=" + ref,
            'lat': float(json_data['latitude']),
            'lon': float(json_data['longitude']),
        }

        hours = self.parse_hours(json_data['hours'])
        if hours:
            properties['opening_hours'] = hours

        yield GeojsonPointItem(**properties)

    def parse(self, response):
        data = response.body_as_unicode()
        store_ids = re.findall(r"[0-9]{5}", data)
        for store_id in store_ids:
            url = "http://www.acehardware.com/storeLocServ?heavy=true&token=ACE&operation=storeData&storeID=%s" % (store_id)
            yield scrapy.Request(
                url,
                callback=self.parse_stores,
                meta={'id': store_id}
            )
