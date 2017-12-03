import json
import re
import scrapy
from locations.items import GeojsonPointItem

class AfcUrgentCareSpider(scrapy.Spider):
    name = "afcurgentcare"
    allowed_domains = ["afcurgentcare.com"]

    def start_requests(self):
        url = 'https://www.afcurgentcare.com/wp-admin/admin-ajax.php'
        headers = {
            'Accept-Language': 'en-US,en;q=0.9',
            'Origin': 'https://www.afcurgentcare.com',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept': '*/*',
            'Referer': 'https://www.afcurgentcare.com/national-map-american-family-care-locations/',
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-Requested-With': 'XMLHttpRequest',
        }
        form_data = {
            'formdata': 'nameSearch=&addressInput=&addressInputCity=&addressInputState=&addressInputCountry=&tag_to_search_for=&radiusSelect=25000&ignore_radius=0',
            'options[initial_results_returned]': '99999',
            'lat': '45',
            'lng': '-122',
            'radius': '25000',
            'action': 'csl_ajax_onload',
        }

        yield scrapy.http.FormRequest(
            url=url, method='POST', formdata=form_data,
            headers=headers, callback=self.parse
        )

    def parse(self, response):
        phoneregex = re.compile('^<a.+>([0-9\-]+)<\/a>$')
        data = json.loads(response.body_as_unicode())
        stores = data['response']
        for store in stores:
            properties = {
                'ref': store['id'],
                'name': store['name'],
                'addr_full': store['address'],
                'city': store['city'],
                'state': store['state'],
                'postcode': store['zip'],
                'lat': store['lat'],
                'lon': store['lng'],
            }
            if store['url']:
                properties['website'] = store['url']
            elif store['sl_pages_url']:
                properties['website'] = store['sl_pages_url']

            if store['phone']:
                phone = phoneregex.match(store['phone'])
                if phone: 
                    phone = phone.groups()[0]
                    properties['phone'] = phone

            yield GeojsonPointItem(**properties)
