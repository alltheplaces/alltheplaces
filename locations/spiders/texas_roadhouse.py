import datetime
import xml.etree.ElementTree as ET

import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours

MAX_RETRIES = 3
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
    allowed_domains = ["www.texasroadhouse.com"]
    download_delay = 0.5
    start_urls = (
        'https://www.texasroadhouse.com/sitefinity/services/LeapFrog/TRH_Proxy.asmx/GetAllStoresDataSet',
    )

    @staticmethod
    def format_address(data):
        addr = " ".join(filter(None, [data["Address1"], data["Address2"]]))
        city = data["City"]
        state = data["State"].strip()
        zip = data["Zip"]
        country = data["Country"]

        if not state and not zip:  # international address - does not have state/zip but may have city
            if city:
                return "{}, {}, {}".format(addr, city, data["Country"])
            else:
                return "{}, {}".format(addr, data["Country"])
        else:
            return "{}, {}, {} {}, {}".format(addr, city, state, zip, country)

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
        retries = 0
        ref = response.meta['id']
        name = response.meta['name']

        try:
            root = ET.fromstring(response.text)
        except ET.ParseError:
            if retries <= MAX_RETRIES:
                retries += 1
                print('Retrying parse store!  store_id: {}'.format(ref))
                yield scrapy.Request(response.url, callback=self.parse_store, dont_filter=True, meta=response.meta)
            else:
                return

        table = root.getchildren()[0]
        data = {i.tag: i.text for i in table}

        if 'Address1' not in data:
            return

        properties = {
            'ref': ref,
            'name': name,
            'addr_full': self.format_address(data),
            'city': (data['City'] or '').strip() or None,
            'state': (data['State'] or '').strip() or None,
            'postcode': (data['Zip'] or '').strip() or None,
            'country': data["Country"].strip(),
            'lat': float(data['GPSLat']),
            'lon': float(data['GPSLon']),
            'phone': data['Phone'],
            'extras': {
                'display_name': data['StoreDisplayName']
            }
        }

        hours = self.parse_hours(data)
        if hours and hours != 'Mo-Su ':
            properties['opening_hours'] = hours

        get_website_url = "https://www.texasroadhouse.com/sitefinity/services/LeapFrog/TRH_Proxy.asmx/GetStoreUrlById?storeID=%s" % (ref)

        yield scrapy.Request(get_website_url,
                             callback=self.parse_website_url,
                             meta={'properties': properties})

    def parse_website_url(self, response):
        retries = 0
        properties = response.meta['properties']

        root = ET.fromstring(response.text)
        website_url = root.text

        if not website_url and retries <= MAX_RETRIES:  # retry if empty
            retries += 1
            print('Retrying parse website url! store_id: {}'.format(properties["ref"]))
            yield scrapy.Request(response.url, callback=self.parse_website_url, dont_filter=True, meta=response.meta)

        if website_url:
            properties["website"] = 'https://www.texasroadhouse.com' + website_url.replace('\n', '')

        yield GeojsonPointItem(**properties)

    def parse(self, response):
        root = ET.fromstring(response.text)

        for table in root.iter('Table'):
            store_id = table.find('StoreID').text
            name = table.find('Name').text
            url = "https://www.texasroadhouse.com/sitefinity/services/LeapFrog/TRH_Proxy.asmx/GetXmlStoreById?storeId=%s" % (store_id)
            yield scrapy.Request(
                url,
                callback=self.parse_store,
                meta={'id': store_id, 'name': name}
            )
