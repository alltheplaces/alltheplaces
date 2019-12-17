# -*- coding: utf-8 -*-
import json
import re
import scrapy

from locations.items import GeojsonPointItem


class BassProSpider(scrapy.Spider):
    name = "basspro"
    download_delay = 0
    allowed_domains = ["basspro.com", "cabelas.com", "cabelas.ca"]
    start_urls = ('https://www.cabelas.com/stores',)

    def parse(self, response):
        brands = {
            'cab': "Cabela's",
            'bps': "Bass Pro Shops"
        }

        script = response.xpath('//script[contains(text(), "var locs")]').extract_first()
        data = re.search(r'var\slocs\s=\s\[(.*?)\];', script).groups()[0]
        data = json.loads('[' + data + ']')

        for store in data:
            lat, lon = store['point'].split(',')

            yield GeojsonPointItem(
                ref=store['key'],
                name=store['name'],
                city=store['address']['city'],
                state=store['address']['region'],
                postcode=store['address']['postalcsode'],
                addr_full=" ".join([store['address']['address1'], store['address'].get('address2', '')]).strip(),
                phone=store['phone'],
                lat=float(lat.strip()),
                lon=float(lon.strip()),
                website=response.urljoin(store["pageurl"]),
                brand=brands[store['brand']],
                extras={
                    "number": store['key']
                }
            )
