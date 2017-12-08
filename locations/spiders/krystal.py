import json
import scrapy
from locations.items import GeojsonPointItem


STATES = ["AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DC", "DE", "FL", "GA",
          "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
          "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
          "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
          "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"]


class KrystalSpider(scrapy.Spider):

    name = "krystal"
    allowed_domains = ["krystal.com"]
    download_delay = 1.5
    start_urls = (
        'http://krystal.com/wp-admin/admin-ajax.php',
    )

    def parse(self, response):
        data = json.loads(response.body_as_unicode())

        for key, store_infor in data.items():
            if isinstance(store_infor, dict):
                properties = {
                    'addr_full': store_infor['address'],
                    'phone': store_infor['phone'],
                    'city': store_infor['city'],
                    'state': store_infor['state'],
                    'postcode': store_infor['zip'],
                    'ref': store_infor['unit'],
                    'website': response.url,
                    'lat': store_infor['lat'],
                    'lon': store_infor['lng']
                }
                yield GeojsonPointItem(**properties)


    def start_requests(self):

        headers = {
                   'Accept-Language': 'en-US,en;q=0.8,ru;q=0.6',
                   'Origin': 'http://krystal.com',
                   'Accept-Encoding': 'gzip, deflate',
                   'Accept': '*/*',
                   'Referer': 'http://krystal.com/locations/',
                   'Connection': 'keep-alive',
                   'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                   'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36'
                   }

        for state in STATES:
            form_data = {'action': 'get_locations_set_by_state', 'data[devicelng]': '-77.2888',
            			 'data[maplng]': '-86.8073','data[maplat]':'32.799',
            			 'data[devicelat]':'38.8318','data[state]': state, 'data[numresults]':'10'}

            yield scrapy.http.FormRequest(url=self.start_urls[0], method='POST',
            							  formdata=form_data, headers=headers,
            							  callback=self.parse)

