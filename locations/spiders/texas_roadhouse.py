import datetime

import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours

DAY_MAPPING = {
    'MonHours': 'Mo',
    'TueHours': 'Tu',
    'WedHours': 'We',
    'ThuHours': 'Th',
    'FriHours': 'Fr',
    'SatHours': 'Sa',
    'SunHours': 'Su'
}


class TexasRoadhouseSpider(scrapy.Spider):
    name = "texas_roadhouse"
    chain_name = "Texas Roadhouse"
    allowed_domains = ["www.texasroadhouse.com"]
    download_delay = 0.5
    start_urls = (
        'https://www.texasroadhouse.com/sitefinity/services/LeapFrog/TRH_Proxy.asmx/GetAllStoresDataSet',
    )

    @staticmethod
    def format_address(address1, address2, city, state, zipcode, country):
        addr = " ".join(filter(None, [address1, address2]))

        if not state and not zipcode:  # international address - does not have state/zip but may have city
            if city:
                return "{}, {}, {}".format(addr, city, country)
            else:
                return "{}, {}".format(addr, country)
        else:
            return "{}, {}, {} {}, {}".format(addr, city, state, zipcode, country)

    @staticmethod
    def convert_to_24hr(date):
        """Convert to 24hour
        Eg: 04:00PM --> 16:00
        """
        return datetime.datetime.strptime(date, '%I:%M%p').strftime('%H:%M')

    def parse_hours(self, data):
        """
        Eg:
        {
            "MonHours": "4:00PM-10:00PM",
            "TueHours": "4:00PM-10:00PM",
            "WedHours": "4:00PM-10:00PM",
            "ThuHours": "4:00PM-10:00PM",
            "FriHours": "4:00PM-11:00PM",
            "SatHours": "11:00AM-11:00PM",
            "SunHours": "11:00AM-10:00PM"
        }
        :param hours:
        :return:
        """
        hours = OpeningHours()
        for k, v in DAY_MAPPING.items():
            open, close = data[k].split('-')
            if not open or not close:
                continue
            hours.add_range(day=v,
                            open_time=self.convert_to_24hr(open),
                            close_time=self.convert_to_24hr(close))

        return hours.as_opening_hours()

    def parse_store(self, response):
        ref = response.meta['id']
        name = response.meta['name']

        address1 = (response.xpath('//Table/Address1/text()').extract_first() or '').strip() or None
        address2 = (response.xpath('//Table/Address2/text()').extract_first() or '').strip() or None
        city = (response.xpath('//Table/City/text()').extract_first() or '').strip()
        state = (response.xpath('//Table/State/text()').extract_first() or '').strip()
        zipcode = (response.xpath('//Table/Zip/text()').extract_first() or '').strip()
        country = (response.xpath('//Table/Country/text()').extract_first() or '').strip()

        if not address1:
            return

        properties = {
            'ref': ref,
            'name': name,
            'addr_full': self.format_address(address1, address2, city, state, zipcode, country),
            'city': city or None,
            'state': state or None,
            'postcode': zipcode or None,
            'country': country or None,
            'lat': float(response.xpath('//Table/GPSLat/text()').extract_first()),
            'lon': float(response.xpath('//Table/GPSLon/text()').extract_first()),
            'phone': response.xpath('//Table/Phone/text()').extract_first(),
            'extras': {
                'display_name': response.xpath('//Table/StoreDisplayName/text()').extract_first()
            }
        }

        hour_data = {day: response.xpath('//Table/{}/text()'.format(day)).extract_first() for day in DAY_MAPPING.keys()}
        hours = self.parse_hours(hour_data)
        if hours and hours != 'Mo-Su ':
            properties['opening_hours'] = hours

        get_website_url = "https://www.texasroadhouse.com/sitefinity/services/LeapFrog/TRH_Proxy.asmx/GetStoreUrlById?storeID=%s" % (ref)

        yield scrapy.Request(get_website_url,
                             callback=self.parse_website_url,
                             meta={'properties': properties})

    def parse_website_url(self, response):
        properties = response.meta['properties']

        website_url = response.xpath('./text()').extract_first()

        if website_url:
            properties["website"] = 'https://www.texasroadhouse.com' + website_url

        yield GeojsonPointItem(**properties)

    def parse(self, response):
        store_elems = response.xpath('//Table')

        for store_elem in store_elems:
            store_id = store_elem.xpath('.//StoreID/text()').extract_first()
            name = store_elem.xpath('.//Name/text()').extract_first()
            url = "https://www.texasroadhouse.com/sitefinity/services/LeapFrog/TRH_Proxy.asmx/GetXmlStoreById?storeId=%s" % (store_id)
            yield scrapy.Request(
                url,
                callback=self.parse_store,
                meta={'id': store_id, 'name': name}
            )
